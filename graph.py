import json
import sqlite3
from dotenv import load_dotenv
import os
load_dotenv()
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from schemas import AgentState
from prompts import SYSTEM_PROMPT, REPLAN_PROMPT, EXECUTE_PROMPT
from langchain_groq import ChatGroq

print("GROQ KEY:", os.getenv("GROQ_API_KEY"))
print("USING MODEL:", os.getenv("MODEL_NAME"))

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

DB_PATH = os.path.join(os.path.dirname(__file__), "inventory.db")

def execute_query(sql: str):
    """Executes a SQL query against the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
        conn.commit()
        return results, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()

def sql_generator_node(state: AgentState):
    """Generates SQL from user input."""
    messages = state.get("messages", [])
    user_question = messages[-1].get("content") if messages else ""
    
    prompt = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User Question: {user_question}")
    ]
    
    response = llm.invoke(prompt)
    
    # Simple extraction of JSON
    content = response.content
    try:
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        else:
            json_str = content.strip()
            
        sql_data = json.loads(json_str)
        generated_sql = sql_data.get("sql", "")
    except Exception as e:
        # Fallback if parsing fails
        generated_sql = ""
        
    return {"generated_sql": generated_sql, "error_message": "", "retry_count": 0}

def execute_sql_node(state: AgentState):
    """Executes the generated SQL."""
    sql = state.get("generated_sql", "")
    
    if not sql:
        return {"error_message": "No SQL generated to execute.", "query_results": []}
        
    results, error = execute_query(sql)
    
    if error:
        return {"error_message": error, "query_results": []}
    
    return {"query_results": results, "error_message": ""}

def sql_correction_node(state: AgentState):
    """Regenerates SQL if execution failed."""
    sql = state.get("generated_sql", "")
    error = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    
    prompt = [
    SystemMessage(content=REPLAN_PROMPT.format(error=error)),
    HumanMessage(content=f"Previous SQL: {sql}")
]
    
    response = llm.invoke(prompt)
    
    try:
         # Simple extraction of JSON
        content = response.content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        else:
            json_str = content.strip()
            
        sql_data = json.loads(json_str)
        corrected_sql = sql_data.get("sql", "")
    except:
        corrected_sql = ""
        
    return {"generated_sql": corrected_sql, "retry_count": retry_count + 1}

def human_response_node(state: AgentState):
    """Formats the final human-readable response."""
    
    messages = state.get("messages", [])
    user_question = messages[-1].get("content") if messages else ""
    sql = state.get("generated_sql", "")
    results = state.get("query_results", [])

    prompt = [
        SystemMessage(content=EXECUTE_PROMPT),
        HumanMessage(content=f"""
User Question: {user_question}

Generated SQL:
{sql}

Database Results:
{json.dumps(results[:10])}
""")
    ]

    response = llm.invoke(prompt)

    content = response.content
    try:
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].strip()
        else:
            json_str = content.strip()
        data = json.loads(json_str)
    except:
        data = {
            "natural_language_answer": content,
            "sql_query": sql
        }

    new_message = {"role": "assistant", "content": data}
    
    # Save to SQLite ChatHistory
    session_id = state.get("session_id", "default")
    if session_id:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("INSERT INTO ChatHistory (SessionId, Role, Content) VALUES (?, ?, ?)", (session_id, 'user', user_question))
            cur.execute("INSERT INTO ChatHistory (SessionId, Role, Content) VALUES (?, ?, ?)", (session_id, 'assistant', data.get("natural_language_answer", str(data))))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to log to SQLite: {e}")

    return {"messages": messages + [new_message]}
    
def route_after_execution(state: AgentState):
    """Route to correction if error, otherwise to human response."""
    error = state.get("error_message", "")
    retry_count = state.get("retry_count", 0)
    
    if error and retry_count < 3:
        return "sql_correction"
    return "human_response"

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("sql_generator", sql_generator_node)
builder.add_node("execute_sql", execute_sql_node)
builder.add_node("sql_correction", sql_correction_node)
builder.add_node("human_response", human_response_node)

builder.set_entry_point("sql_generator")
builder.add_edge("sql_generator", "execute_sql")
builder.add_conditional_edges("execute_sql", route_after_execution)
builder.add_edge("sql_correction", "execute_sql")
builder.add_edge("human_response", END)

graph = builder.compile()

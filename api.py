import os
import sys
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Ensure both bot paths are accessible
base_path = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(base_path, 'inventory_bot')))
sys.path.append(os.path.abspath(os.path.join(base_path, 'knowledge_bot')))

load_dotenv()

from inventory_bot.graph import graph as sql_graph
from knowledge_bot.neo4j_agent import Neo4jAgent

app = FastAPI(title="Unified Chatbot API - Inventory & Knowledge Graph")

# Short Term Memory: Runtime Session Registry
# Format: { session_id: { "sql_state": {...}, "neo4j_agent": Neo4jAgent() } }
sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default_session"

class ChatResponse(BaseModel):
    response: str
    router_decision: str

# Create a master router LLM for distinguishing intent
router_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

def route_query(user_input: str) -> str:
    """Returns 'sql', 'neo4j', or 'chitchat' depending on the query"""
    prompt = [
        SystemMessage(content="""You are a routing assistant for a dual-engine chatbot system.
Your job is to classify the user query into EXACTLY ONE of the following categories:
- "sql": For questions about inventory, stock levels, assets, locations, purchasing, vendors, or sales.
- "neo4j": For questions specifically about employees, companies, who works where, or managing corporate network graphs.
- "chitchat": For casual greetings or completely unrelated topics.

Output ONLY the category name in lowercase."""),
        HumanMessage(content=user_input)
    ]
    response = router_llm.invoke(prompt)
    category = response.content.strip().lower()
    return category if category in ['sql', 'neo4j', 'chitchat'] else 'sql'

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    session_id = request.session_id
    message = request.message
    
    # Initialize short-term memory tracking if missing
    if session_id not in sessions:
        sessions[session_id] = {
            "sql_state": {
                "session_id": session_id,
                "messages": [],
                "generated_sql": "",
                "query_results": [],
                "error_message": "",
                "retry_count": 0
            },
            "neo4j_agent": Neo4jAgent()
        }
    
    session_tracker = sessions[session_id]
    decision = route_query(message)
    
    final_response = ""
    
    if decision == "neo4j":
        neo4j_agent = session_tracker["neo4j_agent"]
        try:
            # Process Neo4j synchronously (offload safely in loop)
            final_response = await asyncio.to_thread(neo4j_agent.process_request, message, session_id)
        except Exception as e:
            final_response = f"Neo4j Agent Error: {str(e)}"
            
    elif decision == "sql":
        state = session_tracker["sql_state"]
        state["messages"].append({"role": "user", "content": message})
        try:
            # Process using langgraph via mapped ainvoke
            new_state = await sql_graph.ainvoke(state)
            session_tracker["sql_state"] = new_state
            
            # Extract final message payload
            messages = new_state.get("messages", [])
            latest_msg = messages[-1]
            content = latest_msg.get("content", "")
            
            if isinstance(content, dict):
                final_response = content.get("natural_language_answer", str(content))
            else:
                final_response = str(content)
        except Exception as e:
            final_response = f"SQL Agent Error: {str(e)}"
    
    else:  # 'chitchat'
        prompt = [SystemMessage(content="You are a friendly assistant. Greet the user casually and nicely."), HumanMessage(content=message)]
        final_response = router_llm.invoke(prompt).content.strip()

    return ChatResponse(response=final_response, router_decision=decision)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

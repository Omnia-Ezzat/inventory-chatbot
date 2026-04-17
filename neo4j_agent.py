import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq

load_dotenv()

class Neo4jAgent:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            self.driver = None

        self.llm = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0
        )
        self.chat_history = []

    def close(self):
        if self.driver:
            self.driver.close()

    def classify_intent(self, user_input: str) -> str:
        prompt = [
            SystemMessage(content="""You are an intent classification assistant for a Knowledge Graph. 
Classify the user's input into EXACTLY ONE of the following categories: chitchat, add, inquire, update, delete.
ONLY return the category name in lowercase without any punctuation or extra text.

Examples:
- "add that Ahmed works at DataHub" -> add
- "who works at DataHub" -> inquire
- "update Ahmed company to OpenAI" -> update
- "delete Ahmed employment" -> delete
- "hello", "how are you", "who are you" -> chitchat
""")
        ] + self.chat_history[-6:] + [
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt)
        return response.content.strip().lower()

    def generate_cypher(self, intent: str, user_input: str) -> str:
        prompt = [
            SystemMessage(content=f"""You are a Cypher query generator for Neo4j.
Generate ONLY a valid Cypher query for the '{intent}' action based on the user's input.
The graph structure is strictly: (Person)-[:WORKS_AT]->(Company)
Nodes have 'name' property.

Do NOT include backticks, markdown formatting, JSON or any explanations. ONLY output the raw Cypher query.

Examples based on intents:
add: MERGE (p:Person {{name:"Ahmed"}}) MERGE (c:Company {{name:"DataHub"}}) MERGE (p)-[:WORKS_AT]->(c) RETURN p.name AS person, c.name AS company
inquire: MATCH (p:Person)-[:WORKS_AT]->(c:Company {{name:"DataHub"}}) RETURN p.name AS person
update: MATCH (p:Person {{name:"Ahmed"}})-[r:WORKS_AT]->() DELETE r MERGE (c:Company {{name:"OpenAI"}}) MERGE (p)-[:WORKS_AT]->(c) RETURN p.name AS person, c.name AS company
delete: MATCH (p:Person {{name:"Ahmed"}})-[r:WORKS_AT]->(c:Company) DELETE r RETURN p.name AS person, c.name AS company
""")
        ] + self.chat_history[-6:] + [
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt)
        cypher = response.content.strip()
        
        # Clean up possible markdown
        if cypher.startswith("```cypher"):
            cypher = cypher[9:].strip()
        elif cypher.startswith("```"):
            cypher = cypher[3:].strip()
        if cypher.endswith("```"):
            cypher = cypher[:-3].strip()
            
        return cypher

    def execute_query(self, query: str):
        if not self.driver:
            return None, "Database connection not available."
            
        try:
            with self.driver.session() as session:
                result = session.run(query)
                records = [record.data() for record in result]
                return records, None
        except Exception as e:
            return None, str(e)

    def generate_response(self, intent: str, user_input: str, records) -> str:
        prompt = [
            SystemMessage(content="""You are a helpful assistant. Formulate a short, natural language response based on the user's action and the database query results.
Do not explain the database structure or the cypher query.
Based on the intent:
- For 'add': confirm that the fact was stored/added.
- For 'update': confirm that the fact was updated.
- For 'delete': confirm that the fact was removed.
- For 'inquire': naturally answer the user's question using the provided records. If the intent is 'inquire' and records are empty, say so. For other intents, empty records mean the operation was successful but returned no data.""")
        ] + self.chat_history[-6:] + [
            HumanMessage(content=f"""User Input: {user_input}
Intent: {intent}
Query Results: {records}""")
        ]
        response = self.llm.invoke(prompt)
        return response.content.strip()

    def _save_interaction(self, session_id: str, user_input: str, response: str):
        self.chat_history.append(HumanMessage(content=user_input))
        self.chat_history.append(AIMessage(content=response))
        
        if not self.driver:
            return
            
        import datetime
        now = datetime.datetime.now().isoformat()
        
        query = """
        MERGE (s:Session {id: $session_id})
        CREATE (m_user:Message {role: 'user', content: $user_input, timestamp: $timestamp})
        CREATE (m_ai:Message {role: 'assistant', content: $response, timestamp: $timestamp})
        CREATE (s)-[:HAS_MESSAGE]->(m_user)
        CREATE (s)-[:HAS_MESSAGE]->(m_ai)
        """
        try:
            with self.driver.session() as session:
                session.run(query, session_id=session_id, user_input=user_input, response=response, timestamp=now)
        except Exception as e:
            print(f"Failed to log interaction to Neo4j: {e}")

    def process_request(self, user_input: str, session_id: str = "default") -> str:
        intent = self.classify_intent(user_input)
        
        if intent == 'chitchat':
            prompt = [
                SystemMessage(content="You are a friendly assistant. Greet the user or respond to casual chat naturally.")
            ] + self.chat_history[-6:] + [
                HumanMessage(content=user_input)
            ]
            final_response = self.llm.invoke(prompt).content.strip()
            self._save_interaction(session_id, user_input, final_response)
            return final_response
            
        if intent not in ['add', 'inquire', 'update', 'delete', 'chitchat']:
            # Maybe the LLM got confused, default to inquire
            intent = 'inquire'
            
        cypher = self.generate_cypher(intent, user_input)
        
        records, error = self.execute_query(cypher)
        
        if error:
            final_response = f"Database error occurred: {error}"
        else:
            final_response = self.generate_response(intent, user_input, records)
        
        self._save_interaction(session_id, user_input, final_response)
        
        return final_response

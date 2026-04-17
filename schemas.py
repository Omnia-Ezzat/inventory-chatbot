from typing import List, Optional, Any, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

# --- LangGraph State ---

class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    generated_sql: str
    query_results: List[Dict[str, Any]]
    error_message: str
    retry_count: int
    session_id: str

# --- API Models ---

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    natural_language_answer: str
    sql_query: str
    token_usage: Dict[str, int]
    latency_ms: float
    provider: str
    model: str
    status: str

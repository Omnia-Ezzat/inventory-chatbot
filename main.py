import time
import json
from fastapi import FastAPI, HTTPException
from schemas import ChatRequest, ChatResponse
from graph import graph
import os

app = FastAPI(
    title="Inventory Data Agent API",
    description="LangGraph + FastAPI Inventory Chatbot"
)

@app.get("/")
def root():
    return {"message": "Server is working"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):

    start_time = time.time()

    initial_state = {
        "messages": [{"role": "user", "content": request.message}],
        "generated_sql": "",
        "query_results": [],
        "error_message": "",
        "retry_count": 0
    }

    try:
        final_state = await graph.ainvoke(initial_state)

        messages = final_state.get("messages", [])
        sql_query = final_state.get("generated_sql", "")

        ai_content = messages[-1]["content"] if messages else {}

        if isinstance(ai_content, dict):
            natural_answer = ai_content.get("natural_language_answer", "")
        else:
            try:
                parsed = json.loads(ai_content)
                natural_answer = parsed.get("natural_language_answer", "")
            except:
                natural_answer = ai_content

        latency_ms = (time.time() - start_time) * 1000

        token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        response = ChatResponse(
            natural_language_answer=natural_answer,
            sql_query=sql_query,
            token_usage=token_usage,
            latency_ms=latency_ms,
            provider="groq",
            model="llama-3.1-8b-instant",
            status="success" if not final_state.get("error_message") else "partial_success"
        )

        return response

    except Exception as e:

        latency_ms = (time.time() - start_time) * 1000

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
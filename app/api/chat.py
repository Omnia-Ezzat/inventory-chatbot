from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.database.connection import engine

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


class Question(BaseModel):
    question: str


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY")
)


def generate_sql(question):

    prompt = f"""
You are an SQL expert.

Convert the user question into SQL.

Database tables:
Assets
Items
Customers
Locations
Vendors

Return ONLY SQL without explanation.

Question:
{question}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    sql = response.content

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    return sql


@router.post("/chat")
def chat(q: Question):

    sql_query = generate_sql(q.question)

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            rows = result.fetchall()
            data = [dict(row._mapping) for row in rows]

        return {
            "question": q.question,
            "sql_query": sql_query,
            "result": data
        }

    except Exception as e:
        return {
            "sql_generated": sql_query,
            "error": str(e)
        }
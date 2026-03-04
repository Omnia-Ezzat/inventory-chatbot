# AI Inventory Chatbot


AI-powered inventory assistant that converts natural language questions into SQL queries and retrieves results from a SQL Server database.

The system allows users to ask questions like *"show all assets"* and automatically generates the correct SQL query using an LLM.

---

## Features

- Natural Language → SQL
- FastAPI REST API
- SQL Server integration
- LLM-powered query generation (Groq / Llama)
- Automatic SQL execution
- Interactive API testing via Swagger

---

## System Architecture
<img width="1000" height="400" alt="Gemini_Generated_Image_nw90bfnw90bfnw90" src="https://github.com/user-attachments/assets/a0021150-54e8-42f4-9631-6df2f6d37f49" />


---

## Project Structure
```
inventory_chatbot
│
├── app
│   ├── api
│   │   └── chat.py
│   │       # API endpoint for user questions
│   │
│   ├── database
│   │   └── connection.py
│   │       # SQL Server connection using SQLAlchemy
│   │
│   ├── repositories
│   │   └── inventory_repository.py
│   │       # Database query logic
│   │
│   └── main.py
│       # FastAPI application entry point
│
└── requirements.txt
    # Project dependencies
```

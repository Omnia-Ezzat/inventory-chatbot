from sqlalchemy import create_engine

DATABASE_URL = (
    "mssql+pyodbc://localhost/invenDB?"
    "driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
)

engine = create_engine(DATABASE_URL)
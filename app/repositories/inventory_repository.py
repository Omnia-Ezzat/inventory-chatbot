from sqlalchemy import text
from app.database.connection import engine


def get_all_assets():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM Assets"))
        rows = result.fetchall()

        data = []
        for row in rows:
            data.append(dict(row._mapping))

        return data


def get_all_items():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM Items"))
        rows = result.fetchall()

        data = []
        for row in rows:
            data.append(dict(row._mapping))

        return data
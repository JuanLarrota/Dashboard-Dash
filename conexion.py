import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(".env.local")
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("No se encontró DATABASE_URL en el archivo .env.local")

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-c default_transaction_read_only=on"},
)


def consultar(sql):
    return pd.read_sql(sql, engine)


if __name__ == "__main__":
    tablas = consultar("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    print(tablas)

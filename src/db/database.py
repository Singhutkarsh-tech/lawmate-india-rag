import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent/"lawmate.db"
SCHEMA_PATH = Path(__file__).resolve().parent/"schema.sql"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  #sqlite3 returns data as tuple and to make it better accessable it is best to convert it into a dict.
    return conn

def init__db():
    with get_conn() as conn, open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    print(f"Database Schema Initiated")

if __name__ == "__main__":
    init__db()
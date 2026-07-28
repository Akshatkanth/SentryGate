import sqlite3
from typing import Generator

DATABASE_URL = "sentrygate.db"

def init_db():
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_id TEXT,
            user_input TEXT,
            input_blocked BOOLEAN,
            input_block_reason TEXT,
            input_block_category TEXT
        )
    """)
    
    # Create responses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER,
            timestamp TEXT,
            llm_output TEXT,
            output_blocked BOOLEAN,
            output_block_reason TEXT,
            output_block_category TEXT,
            final_response TEXT,
            FOREIGN KEY(request_id) REFERENCES requests(id)
        )
    """)
    
    # Create eval_runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eval_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            test_case_id TEXT,
            category TEXT,
            expected TEXT,
            actual TEXT,
            passed BOOLEAN
        )
    """)
    
    conn.commit()
    conn.close()

def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DATABASE_URL, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

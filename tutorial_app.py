from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

DB_PATH = "sentrygate_tutorial.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            input_blocked BOOLEAN,
            input_block_reason TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()  # runs once when the module is imported


class ChatRequest(BaseModel):
    user_id: str
    message: str


class GuardrailResult(BaseModel):
    blocked: bool
    reason: Optional[str] = None
    category: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    input_guardrail: GuardrailResult
    output_guardrail: GuardrailResult


@app.get("/health")
def health_check():
    return {"status": "ok"}


def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def check_input(message: str) -> GuardrailResult:
    if "ignore previous instructions" in message.lower():
        return GuardrailResult(blocked=True, reason="prompt injection phrase", category="injection")
    return GuardrailResult(blocked=False)


def check_output(reply: str) -> GuardrailResult:
    return GuardrailResult(blocked=False)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    input_result = check_input(request.message)

    if input_result.blocked:
        reply = "I can't help with that request."
    else:
        reply = f"Simulated bot reply to: {request.message}"

    output_result = check_output(reply)

    db.execute(
        "INSERT INTO requests (user_input, input_blocked, input_block_reason) VALUES (?, ?, ?)",
        (request.message, input_result.blocked, input_result.reason),
    )
    db.commit()

    return ChatResponse(
        reply=reply,
        input_guardrail=input_result,
        output_guardrail=output_result,
    )
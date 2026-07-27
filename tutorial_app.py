from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

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

def get_db():
    conn = sqlite3.connect("sentrygate.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def check_input(message: str) -> GuardrailResult:
    # placeholder — real regex/keyword logic comes in Phase 2
    if "ignore previous instructions" in message.lower():
        return GuardrailResult(blocked=True, reason="prompt injection phrase", category="injection")
    return GuardrailResult(blocked=False)

def check_output(reply: str) -> GuardrailResult:
    # placeholder — real logic comes in Phase 5
    return GuardrailResult(blocked=False)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    input_result = check_input(request.message)

    if input_result.blocked:
        reply = "I can't help with that request."
    else:
        reply = f"Simulated bot reply to: {request.message}"  # Groq call goes here later

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
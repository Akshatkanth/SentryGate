import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, timezone
import sqlite3

from db import init_db, get_db
from guardrails.models import GuardrailResult
from guardrails.input_rules import check_input
from guardrails.input_llm import check_input_llm
from guardrails.output_rules import check_output_rules
from guardrails.output_llm import check_output_llm
from bot.support_bot import generate_reply

# Load environment variables (doesn't crash if .env is missing)
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    init_db()
    yield
    # Shutdown logic (if any) can go here

app = FastAPI(title="SentryGate", lifespan=lifespan)

@app.get("/health")
def health_check():
    return {"status": "ok"}

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    input_guardrail: GuardrailResult
    output_guardrail: GuardrailResult

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    # 1 & 2: Input Guardrails
    input_result = check_input(request.message)
    if not input_result.blocked:
        input_result = check_input_llm(request.message)

    if input_result.blocked:
        final_reply = "I can't help with that request."
        llm_output = None
        output_result = GuardrailResult(blocked=False)
    else:
        # 3. Generate raw reply
        llm_output = generate_reply(request.message)
        
        # 4. Output Guardrails
        output_result = check_output_rules(llm_output)
        if not output_result.blocked:
            output_result = check_output_llm(llm_output)
            
        if output_result.blocked:
            final_reply = "I'm not able to provide that. Let me connect you with a human agent."
        else:
            final_reply = llm_output

    # 5. Log Request
    cursor = db.cursor()
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        INSERT INTO requests (timestamp, user_id, user_input, input_blocked, input_block_reason, input_block_category)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        now,
        request.user_id,
        request.message,
        input_result.blocked,
        input_result.reason,
        input_result.category
    ))
    request_id = cursor.lastrowid
    db.commit()

    # 6. Log Response
    cursor.execute("""
        INSERT INTO responses (request_id, timestamp, llm_output, output_blocked, output_block_reason, output_block_category, final_response)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        request_id,
        datetime.now(timezone.utc).isoformat(),
        llm_output,
        output_result.blocked,
        output_result.reason,
        output_result.category,
        final_reply
    ))
    db.commit()

    # 7. Return Response
    return ChatResponse(
        reply=final_reply,
        input_guardrail=input_result,
        output_guardrail=output_result
    )

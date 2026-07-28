import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from db import init_db

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

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Depends
from fastapi import HTTPException

import time
from fastapi import Request

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    blocked: bool


def get_db():
    conn = sqlite3.connect("sentrygate.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

@app.post("/chat", response_model=ChatResponse)

@app.middleware("http")
async def log_timing(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    print(f"{request.method} {request.url.path} took {duration_ms:.1f}ms")
    return response

def chat(request: ChatRequest, db: sqlite3.Connection = Depends(get_db)):
    db.execute(
        "INSERT INTO requests (user_input) VALUES (?)",
        (request.message,)
    )
    db.commit()
    ...
@app.get("/requests/{request_id}")
def get_request(request_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT * FROM requests WHERE id = ?", (request_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return dict(row)
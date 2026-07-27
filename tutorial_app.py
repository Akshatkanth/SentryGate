from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    blocked: bool

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    # request.message is guaranteed to be a string, request.user_id too
    if "ignore previous instructions" in request.message.lower():
        return ChatResponse(reply="Request blocked.", blocked=True)
    return ChatResponse(reply=f"Echo: {request.message}", blocked=False)


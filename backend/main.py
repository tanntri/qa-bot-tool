from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
import sys

# Add project root to Python path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.graphs.graphs import get_response_from_rag

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's question about bugs or feedback")

class ChatResponse(BaseModel):
    question: str
    answer: str
    success: bool
    error: Optional[str] = None

@app.get("/")
async def root():
    return {"message": "Welcome to the Internal QA Tool API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        answer = await get_response_from_rag(request.question)
        return ChatResponse(
            question=request.question,
            answer=answer,
            success=True
        )
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
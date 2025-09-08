from fastapi import APIRouter
import requests

router = APIRouter()

# Ollama server endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:1.5b"  

@router.post("/chat/")
async def chat_with_ai(prompt: str):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False  # set to True if you want streaming responses
    }

    response = requests.post(OLLAMA_API_URL, json=payload)
    data = response.json()

    return {"reply": data.get("response", "")}

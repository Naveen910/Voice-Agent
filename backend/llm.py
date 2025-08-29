from fastapi import APIRouter
import google.generativeai as genai

router = APIRouter()

# Directly configure with your key
GEMINI_API_KEY = "AIzaSyBgTqN1AiBhiJZHT0CvV1jx-c099r3fMLs"  
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

@router.post("/chat/")
async def chat_with_ai(prompt: str):
    response = model.generate_content(prompt)
    return {"reply": response.text}

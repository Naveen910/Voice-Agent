from fastapi import APIRouter
from fastapi.responses import FileResponse
import pyttsx3
import tempfile

router = APIRouter()

@router.post("/tts/")
async def synthesize_text(text: str):
    """
    Convert text to speech and return an audio file
    """
    if not text.strip():
        return {"error": "Text cannot be empty"}

    engine = pyttsx3.init()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    engine.save_to_file(text, tmp.name)
    engine.runAndWait()

    return FileResponse(tmp.name, media_type="audio/mpeg", filename="output.mp3")

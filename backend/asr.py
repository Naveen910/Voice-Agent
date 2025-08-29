from fastapi import APIRouter, UploadFile, File, HTTPException
import speech_recognition as sr
import tempfile

router = APIRouter()

@router.post("/asr/")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Upload an audio file (wav/mp3) and get transcription
    """
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

    # Save to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    recognizer = sr.Recognizer()
    with sr.AudioFile(tmp_path) as source:
        audio_data = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        text = "[Unintelligible audio]"
    except sr.RequestError:
        raise HTTPException(status_code=500, detail="ASR service unavailable")

    return {"transcription": text}

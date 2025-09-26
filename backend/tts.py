# tts.py
import io
import subprocess
import json
from TTS.api import TTS
from pydub import AudioSegment

# Initialize Coqui TTS
tts = TTS(model_name="tts_models/en/vctk/vits")

def generate_tts_audio(text: str) -> bytes:
    """
    Generate mp3 audio bytes from text using Coqui TTS.
    """
    wav_path = "temp.wav"
    mp3_path = "temp.mp3"
    
    tts.tts_to_file(text=text, file_path=wav_path)
    
    # Convert WAV → MP3 for browser
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3")
    
    return open(mp3_path, "rb").read()


def generate_lipsync_cues(text: str, audio_bytes: bytes) -> list:
    """
    Generate mouth cues using Rhubarb Lip Sync.
    Returns list of {start, end, value} with values like A,B,C...
    """
    # Save audio temporarily
    audio_path = "temp_audio.wav"
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    
    # Run Rhubarb CLI
    result_path = "temp_lipsync.json"
    subprocess.run([
        "rhubarb", audio_path, "-o", result_path, "--srt"  # can output JSON too
    ], check=True)
    
    # Parse Rhubarb JSON output
    with open(result_path, "r") as f:
        data = json.load(f)
    
    # Rhubarb uses viseme names like PP, FF, etc.
    cues = []
    for item in data["mouthCues"]:
        cues.append({
            "start": item["start"],
            "end": item["end"],
            "value": item["value"]  # will map to morph targets in Avatar.jsx
        })
    return cues

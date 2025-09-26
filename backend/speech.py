import io
import subprocess
import json
from TTS.api import TTS
from pydub import AudioSegment
import os

# Ensure temp folder exists
os.makedirs("temp", exist_ok=True)

# Initialize Coqui TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

def generate_tts_audio(text: str) -> tuple[bytes, bytes]:
    """
    Generate TTS audio.
    Returns a tuple: (mp3_bytes_for_browser, wav_bytes_for_rhubarb)
    """
    wav_path = "temp/temp.wav"
    mp3_path = "temp/temp.mp3"

    # Generate WAV from TTS
    tts.tts_to_file(text=text, file_path=wav_path)

    # Convert WAV -> MP3
    audio = AudioSegment.from_wav(wav_path)
    audio.export(mp3_path, format="mp3")

    # Read bytes
    mp3_bytes = open(mp3_path, "rb").read()
    wav_bytes = open(wav_path, "rb").read()  # proper WAV for Rhubarb

    return mp3_bytes, wav_bytes


def generate_lipsync_cues(text: str, wav_bytes: bytes) -> list:
    """
    Generate mouth cues using Rhubarb Lip Sync.
    Expects properly formatted WAV bytes.
    Returns list of {start, end, value}.
    """
    wav_path = "temp/temp_for_rhubarb.wav"
    with open(wav_path, "wb") as f:
        f.write(wav_bytes)

    result_path = "temp/temp_lipsync.json"

    subprocess.run([
        "rhubarb",
        "-f", "json",          # correct flag
        "-o", result_path,
        wav_path
    ], check=True)

    with open(result_path, "r") as f:
        data = json.load(f)

    cues = [
        {"start": item["start"], "end": item["end"], "value": item["value"]}
        for item in data["mouthCues"]
    ]
    return cues

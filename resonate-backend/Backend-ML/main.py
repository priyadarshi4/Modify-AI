from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import os
import whisper
import threading
import tempfile
import traceback
import asyncio
import json
import httpx
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt

# -----------------------------------------------------------------------------
# App & Env
# -----------------------------------------------------------------------------

app = FastAPI()
load_dotenv()

# -----------------------------------------------------------------------------
# Whisper Setup (Thread Safe)
# -----------------------------------------------------------------------------

try:
    whisper_model = whisper.load_model("base")
    whisper_model_lock = threading.Lock()
    print("✅ Whisper model loaded")
except Exception as e:
    print("❌ Whisper load failed:", e)
    whisper_model = None

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

API_URL = os.getenv("LLAMA_MODELURL", "http://localhost:11434/v1/chat/completions")

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------

class TranscriptPayload(BaseModel):
    transcript: str

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def extract_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    except Exception:
        return None
    return None

def encrypt_transcription(text: str):
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        return {"status": False, "message": "Encryption key missing"}

    try:
        salt = b"salt"
        key = scrypt(
            encryption_key.encode(),
            salt,
            key_len=32,
            N=16384,
            r=8,
            p=1
        )
        iv = os.urandom(16)
        cipher = AES.new(key, AES.MODE_CBC, iv)

        data = text.encode()
        pad_len = AES.block_size - len(data) % AES.block_size
        padded = data + bytes([pad_len] * pad_len)

        encrypted = cipher.encrypt(padded)
        return {
            "status": True,
            "transcription": f"{iv.hex()}:{encrypted.hex()}"
        }

    except Exception as e:
        return {"status": False, "message": str(e)}

# -----------------------------------------------------------------------------
# Ollama Analysis Helpers
# -----------------------------------------------------------------------------

async def ollama_call(client, system_prompt, user_text):
    payload = {
        "model": "gemma:2b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }
    res = await client.post(API_URL, json=payload)
    data = res.json()
    return extract_json(data["choices"][0]["message"]["content"])

async def get_full_analysis(text: str):
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            tasks = [
                ollama_call(
                    client,
                    "Return JSON with ai_summary and tags (3-5 keywords).",
                    text
                ),
                ollama_call(
                    client,
                    "Return JSON mood scores (joy,sadness,anger,fear,surprise,love,calm).",
                    text
                ),
                ollama_call(
                    client,
                    "Return JSON with reflections and suggestions.",
                    text
                ),
                ollama_call(
                    client,
                    "Return JSON with key 'goal' or null.",
                    text
                ),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        final = {}
        for r in results:
            if isinstance(r, dict):
                final.update(r)

        return final

    except Exception as e:
        print("❌ Analysis failed:", e)
        return None

# -----------------------------------------------------------------------------
# API Endpoints
# -----------------------------------------------------------------------------

@app.post("/transcribe")
async def transcribe_audio(audio: bytes = Body(...)):
    if not whisper_model:
        raise HTTPException(status_code=503, detail="Whisper not available")

    audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio)
            audio_path = f.name

        with whisper_model_lock:
            result = whisper_model.transcribe(audio_path)

        return encrypt_transcription(result["text"])

    except Exception as e:
        print("❌ TRANSCRIPTION ERROR")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)

@app.post("/analysis_transcript")
async def analysis_transcript(payload: TranscriptPayload):
    analysis = await get_full_analysis(payload.transcript)

    if not analysis:
        return {"status": False, "message": "AI analysis failed"}

    required = ["ai_summary", "tags", "mood", "reflections", "suggestions", "goal"]
    if not all(k in analysis for k in required):
        return {"status": False, "message": "Incomplete AI response"}

    return {
        "status": True,
        "results": analysis
    }

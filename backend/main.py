import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.intent_parser import TaskIntent, parse_transcript
from backend.voice_pipeline import transcribe_audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Voice Browser Agent API starting up")
    yield
    logger.info("Voice Browser Agent API shutting down")


app = FastAPI(
    title="Voice Browser Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    transcript: str


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/parse", response_model=TaskIntent, summary="Parse a text transcript into a TaskIntent")
async def parse_text(request: ParseRequest):
    """
    Accept a plain-text voice transcript and return a validated TaskIntent JSON.

    - **action_type**: primary browser action
    - **reversibility**: read | reversible | irreversible
    - **requires_confirmation**: true for all irreversible actions (HITL gate)
    - **ambiguity_flags**: non-empty when the command is unclear
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="transcript must not be empty")
    try:
        return await parse_transcript(request.transcript)
    except Exception as exc:
        logger.exception("Intent parsing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/parse/audio",
    response_model=TaskIntent,
    summary="Transcribe audio via Whisper then parse into a TaskIntent",
)
async def parse_audio(audio: UploadFile = File(...)):
    """
    Accept a WAV/MP3/M4A/OGG audio file, transcribe with Whisper-1, then parse intent.
    The `raw_transcript` field in the response contains the Whisper output.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="audio file is empty")
    try:
        transcript = await transcribe_audio(audio_bytes, filename=audio.filename or "audio.wav")
        intent = await parse_transcript(transcript)
        intent.raw_transcript = transcript
        return intent
    except Exception as exc:
        logger.exception("Audio transcription or parsing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

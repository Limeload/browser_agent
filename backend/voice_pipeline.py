import io
import os
import openai

_client: openai.AsyncOpenAI | None = None


def _get_client() -> openai.AsyncOpenAI:
    global _client
    if _client is None:
        _client = openai.AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    """Transcribe raw audio bytes to text using OpenAI Whisper-1."""
    client = _get_client()

    buf = io.BytesIO(audio_bytes)
    buf.name = filename  # Whisper infers format from the extension

    transcript = await client.audio.transcriptions.create(
        model="whisper-1",
        file=buf,
        response_format="text",
    )
    # response_format="text" returns a plain str, not a Transcription object
    return str(transcript).strip()

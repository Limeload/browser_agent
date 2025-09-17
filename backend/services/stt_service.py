"""
Speech-to-Text Service
Handles audio processing and transcription using multiple STT providers
"""

import asyncio
import io
import os
import tempfile
from typing import Optional, Dict, Any, Tuple
import structlog
import whisper
import deepgram
from google.cloud import speech
from models.schemas import AudioChunk, TranscriptResponse
from services.monitoring import MonitoringService

logger = structlog.get_logger()

class STTService:
    def __init__(self, monitoring_service: MonitoringService):
        self.monitoring_service = monitoring_service
        self.whisper_model = None
        self.deepgram_client = None
        self.google_client = None
        self.provider = os.getenv("STT_PROVIDER", "whisper")
        
    async def initialize(self):
        """Initialize STT providers"""
        logger.info("Initializing STT service", provider=self.provider)
        
        try:
            if self.provider == "whisper":
                await self._init_whisper()
            elif self.provider == "deepgram":
                await self._init_deepgram()
            elif self.provider == "google":
                await self._init_google()
            else:
                raise ValueError(f"Unsupported STT provider: {self.provider}")
                
            logger.info("STT service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize STT service", error=str(e))
            raise
    
    async def _init_whisper(self):
        """Initialize Whisper model"""
        model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        logger.info("Loading Whisper model", size=model_size)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        self.whisper_model = await loop.run_in_executor(
            None, whisper.load_model, model_size
        )
        
    async def _init_deepgram(self):
        """Initialize Deepgram client"""
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY environment variable is required")
            
        self.deepgram_client = deepgram.DeepgramClient(api_key)
        
    async def _init_google(self):
        """Initialize Google Speech client"""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is required")
            
        self.google_client = speech.SpeechClient()
    
    async def process_audio(self, audio_chunk: AudioChunk) -> TranscriptResponse:
        """Process audio chunk and return transcript"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info("Processing audio chunk", 
                       session_id=audio_chunk.session_id,
                       size_bytes=len(audio_chunk.audio_data))
            
            # Record metrics
            await self.monitoring_service.record_metric(
                "stt_audio_chunk_size", 
                len(audio_chunk.audio_data),
                {"session_id": audio_chunk.session_id}
            )
            
            transcript = ""
            confidence = 0.0
            
            if self.provider == "whisper":
                transcript, confidence = await self._transcribe_whisper(audio_chunk)
            elif self.provider == "deepgram":
                transcript, confidence = await self._transcribe_deepgram(audio_chunk)
            elif self.provider == "google":
                transcript, confidence = await self._transcribe_google(audio_chunk)
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Record processing time metric
            await self.monitoring_service.record_metric(
                "stt_processing_time",
                processing_time,
                {"session_id": audio_chunk.session_id, "provider": self.provider}
            )
            
            response = TranscriptResponse(
                session_id=audio_chunk.session_id,
                transcript=transcript,
                confidence=confidence,
                is_final=True,
                processing_time=processing_time
            )
            
            logger.info("Audio transcription completed",
                       session_id=audio_chunk.session_id,
                       transcript_length=len(transcript),
                       confidence=confidence,
                       processing_time=processing_time)
            
            return response
            
        except Exception as e:
            logger.error("STT processing failed", 
                        error=str(e), 
                        session_id=audio_chunk.session_id)
            
            # Record error metric
            await self.monitoring_service.record_metric(
                "stt_errors",
                1,
                {"session_id": audio_chunk.session_id, "error_type": type(e).__name__}
            )
            
            raise
    
    async def _transcribe_whisper(self, audio_chunk: AudioChunk) -> Tuple[str, float]:
        """Transcribe using Whisper"""
        if not self.whisper_model:
            raise RuntimeError("Whisper model not initialized")
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(audio_chunk.audio_data)
            temp_file_path = temp_file.name
        
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self.whisper_model.transcribe, temp_file_path
            )
            
            transcript = result["text"].strip()
            confidence = 1.0  # Whisper doesn't provide confidence scores
            
            return transcript, confidence
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    async def _transcribe_deepgram(self, audio_chunk: AudioChunk) -> Tuple[str, float]:
        """Transcribe using Deepgram"""
        if not self.deepgram_client:
            raise RuntimeError("Deepgram client not initialized")
        
        # Configure Deepgram options
        options = deepgram.PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="en-US"
        )
        
        # Send audio for transcription
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                {"buffer": audio_chunk.audio_data, "mimetype": "audio/wav"},
                options
            )
        )
        
        if response.results.channels:
            channel = response.results.channels[0]
            if channel.alternatives:
                alternative = channel.alternatives[0]
                transcript = alternative.transcript
                confidence = alternative.confidence
                return transcript, confidence
        
        return "", 0.0
    
    async def _transcribe_google(self, audio_chunk: AudioChunk) -> Tuple[str, float]:
        """Transcribe using Google Speech-to-Text"""
        if not self.google_client:
            raise RuntimeError("Google Speech client not initialized")
        
        # Configure audio
        audio = speech.RecognitionAudio(content=audio_chunk.audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=audio_chunk.sample_rate or 44100,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        # Perform transcription
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.google_client.recognize(config=config, audio=audio)
        )
        
        if response.results:
            result = response.results[0]
            transcript = result.alternatives[0].transcript
            confidence = result.alternatives[0].confidence
            return transcript, confidence
        
        return "", 0.0
    
    def is_healthy(self) -> bool:
        """Check if STT service is healthy"""
        try:
            if self.provider == "whisper":
                return self.whisper_model is not None
            elif self.provider == "deepgram":
                return self.deepgram_client is not None
            elif self.provider == "google":
                return self.google_client is not None
            return False
        except Exception:
            return False

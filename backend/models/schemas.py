"""
Pydantic models for the Voice-Enabled Browser Agent
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class ActionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    NAVIGATE = "navigate"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    EXTRACT_TEXT = "extract_text"
    EXTRACT_LINKS = "extract_links"

class IntentType(str, Enum):
    NAVIGATION = "navigation"
    FORM_FILLING = "form_filling"
    DATA_EXTRACTION = "data_extraction"
    SEARCH = "search"
    CLICK_ACTION = "click_action"
    SCROLL_ACTION = "scroll_action"
    UNKNOWN = "unknown"

class AudioChunk(BaseModel):
    session_id: str
    audio_data: bytes
    timestamp: float
    sample_rate: Optional[int] = 44100
    channels: Optional[int] = 1

class TranscriptResponse(BaseModel):
    session_id: str
    transcript: str
    confidence: float
    is_final: bool
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: float

class IntentResponse(BaseModel):
    session_id: str
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any] = Field(default_factory=dict)
    raw_text: str
    parsed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)
    processing_time: float

class BrowserAction(BaseModel):
    action_type: ActionType
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    xpath: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    wait_time: Optional[float] = None
    retry_count: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExecutionRequest(BaseModel):
    session_id: str
    actions: List[BrowserAction]
    context: Dict[str, Any] = Field(default_factory=dict)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

class ExecutionResponse(BaseModel):
    session_id: str
    success: bool
    actions_executed: List[BrowserAction]
    screenshots: List[str] = Field(default_factory=list)
    final_url: Optional[str] = None
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class SessionData(BaseModel):
    session_id: str
    start_time: datetime = Field(default_factory=datetime.now)
    transcripts: List[TranscriptResponse] = Field(default_factory=list)
    intents: List[IntentResponse] = Field(default_factory=list)
    executions: List[ExecutionResponse] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True

class MonitoringMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    service_name: str
    metric_name: str
    value: Union[float, int, str]
    tags: Dict[str, str] = Field(default_factory=dict)

class LogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    level: str
    service: str
    message: str
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ExportData(BaseModel):
    session_id: str
    export_timestamp: datetime = Field(default_factory=datetime.now)
    transcripts: List[TranscriptResponse]
    intents: List[IntentResponse]
    executions: List[ExecutionResponse]
    screenshots: List[str]
    metadata: Dict[str, Any] = Field(default_factory=dict)

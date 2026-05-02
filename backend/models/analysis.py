from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime


class PitchResult(BaseModel):
    """Single pitch detection result"""
    time: float
    frequency: float
    note: str
    octave: int
    cents: int
    volume: float
    confidence: float = 1.0


class AnalysisResponse(BaseModel):
    """Full audio analysis response"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: float
    sample_rate: int
    pitch_data: List[PitchResult]
    average_frequency: float
    dominant_note: str
    instrument: str = "chromatic"


class RecordingHistory(BaseModel):
    """Recording history item"""
    id: str
    timestamp: datetime
    duration: float
    dominant_note: str
    average_frequency: float
    mode: str
    instrument: str = "chromatic"
    has_audio: bool = False


class AudioAnalyzeRequest(BaseModel):
    """Request model for audio analysis"""
    audio_base64: str
    sample_rate: int = 44100
    mode: str = "tuner"
    instrument: str = "chromatic"
    save_audio: bool = False


class RealtimeAnalyzeRequest(BaseModel):
    """Request model for real-time analysis"""
    audio_base64: str
    sample_rate: int = 44100
    instrument: str = "chromatic"


class InstrumentProfile(BaseModel):
    """Instrument profile model"""
    id: str
    name: str
    strings: List[dict]
    freq_range: List[int]
from fastapi import APIRouter, HTTPException
import logging
import base64
import numpy as np

from models.analysis import (
    AudioAnalyzeRequest,
    RealtimeAnalyzeRequest,
    AnalysisResponse,
    PitchResult,
    RecordingHistory,
    InstrumentProfile
)
from services.pitch_detection import analyze_audio_data_advanced, analyze_realtime
from services.note_mapper import (
    frequency_to_note,
    find_closest_string,
    get_instrument_profile,
    get_all_instruments,
    INSTRUMENT_PROFILES
)
from db.mongo import recordings_collection
from typing import List

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Audio Analysis API v2.0 - Enhanced with PYIN"}


@router.get("/instruments", response_model=List[InstrumentProfile])
async def get_instruments():
    """Get all available instrument profiles"""
    instruments = get_all_instruments()
    return [
        InstrumentProfile(
            id=key,
            name=profile["name"],
            strings=profile["strings"],
            freq_range=profile["freq_range"]
        )
        for key, profile in instruments.items()
    ]


@router.get("/instruments/{instrument_id}")
async def get_instrument(instrument_id: str):
    """Get a specific instrument profile"""
    profile = get_instrument_profile(instrument_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Instrument not found")
    
    return {
        "id": instrument_id,
        "name": profile["name"],
        "strings": profile["strings"],
        "freq_range": profile["freq_range"]
    }


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_audio(request: AudioAnalyzeRequest):
    """Analyze audio data and return pitch information"""
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio data")
        
        sample_rate = request.sample_rate
        duration = len(audio_data) / sample_rate
        
        # Use advanced analysis
        pitch_data = analyze_audio_data_advanced(audio_data, sample_rate, request.instrument)
        
        # Calculate statistics
        valid_freqs = [p["frequency"] for p in pitch_data if p["frequency"] > 0]
        avg_freq: float = float(np.mean(valid_freqs)) if valid_freqs else 0.0
        
        if valid_freqs:
            dominant_note_info = frequency_to_note(avg_freq)
            dominant_note = f"{dominant_note_info['note']}{dominant_note_info['octave']}"
        else:
            dominant_note = "--"
        
        result = AnalysisResponse(
            duration=float(round(duration, 2)),
            sample_rate=sample_rate,
            pitch_data=[PitchResult(**p) for p in pitch_data],
            average_frequency=float(round(avg_freq, 2)),
            dominant_note=dominant_note,
            instrument=request.instrument
        )
        
        # Save to database
        history_entry = {
            "id": result.id,
            "timestamp": result.timestamp,
            "duration": result.duration,
            "dominant_note": result.dominant_note,
            "average_frequency": result.average_frequency,
            "mode": request.mode,
            "instrument": request.instrument,
            "pitch_data": pitch_data[:200],
            "has_audio": request.save_audio
        }
        
        # Optionally save audio for playback
        if request.save_audio:
            history_entry["audio_base64"] = request.audio_base64
        
        await recordings_collection.insert_one(history_entry)
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-realtime")
async def analyze_realtime_endpoint(request: RealtimeAnalyzeRequest):
    """Analyze a short audio buffer for real-time feedback"""
    try:
        audio_bytes = base64.b64decode(request.audio_base64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
        
        if len(audio_data) == 0:
            return {
                "note": "--", "octave": 0, "cents": 0, "frequency": 0,
                "volume": 0, "confidence": 0, "target_string": None
            }
        
        result = analyze_realtime(audio_data, request.sample_rate, request.instrument)
        
        # Find closest string for instrument tuning
        target_string = None
        if result["frequency"] > 0:
            target_string = find_closest_string(result["frequency"], request.instrument)
        
        result["target_string"] = target_string
        return result
        
    except Exception as e:
        logger.error(f"Real-time analysis error: {str(e)}")
        return {
            "note": "--", "octave": 0, "cents": 0, "frequency": 0,
            "volume": 0, "confidence": 0, "target_string": None
        }


@router.get("/history", response_model=List[RecordingHistory])
async def get_history(limit: int = 50):
    """Get recording history"""
    recordings = await recordings_collection.find().sort("timestamp", -1).limit(limit).to_list(limit)
    return [
        RecordingHistory(
            id=r["id"],
            timestamp=r["timestamp"],
            duration=r["duration"],
            dominant_note=r["dominant_note"],
            average_frequency=r["average_frequency"],
            mode=r.get("mode", "tuner"),
            instrument=r.get("instrument", "chromatic"),
            has_audio=r.get("has_audio", False)
        )
        for r in recordings
    ]


@router.get("/history/{recording_id}")
async def get_recording(recording_id: str):
    """Get a specific recording with pitch data"""
    recording = await recordings_collection.find_one({"id": recording_id})
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    recording["_id"] = str(recording["_id"])
    return recording


@router.get("/history/{recording_id}/audio")
async def get_recording_audio(recording_id: str):
    """Get the audio data for a recording (for playback)"""
    recording = await recordings_collection.find_one({"id": recording_id})
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if not recording.get("audio_base64"):
        raise HTTPException(status_code=404, detail="Audio not available for this recording")
    
    return {
        "audio_base64": recording["audio_base64"],
        "sample_rate": recording.get("sample_rate", 44100),
        "duration": recording["duration"]
    }


@router.delete("/history/{recording_id}")
async def delete_recording(recording_id: str):
    """Delete a recording"""
    result = await recordings_collection.delete_one({"id": recording_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recording not found")
    return {"message": "Recording deleted"}


@router.delete("/history")
async def clear_history():
    """Clear all recording history"""
    result = await recordings_collection.delete_many({})
    return {"message": f"Deleted {result.deleted_count} recordings"}

import numpy as np
from typing import Optional

# Musical note frequencies (A4 = 440Hz standard)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Instrument tuning profiles
INSTRUMENT_PROFILES = {
    "guitar_standard": {
        "name": "Guitar (Standart)",
        "strings": [
            {"note": "E", "octave": 2, "frequency": 82.41},
            {"note": "A", "octave": 2, "frequency": 110.00},
            {"note": "D", "octave": 3, "frequency": 146.83},
            {"note": "G", "octave": 3, "frequency": 196.00},
            {"note": "B", "octave": 3, "frequency": 246.94},
            {"note": "E", "octave": 4, "frequency": 329.63},
        ],
        "freq_range": [70, 400]
    },
    "guitar_drop_d": {
        "name": "Guitar (Drop D)",
        "strings": [
            {"note": "D", "octave": 2, "frequency": 73.42},
            {"note": "A", "octave": 2, "frequency": 110.00},
            {"note": "D", "octave": 3, "frequency": 146.83},
            {"note": "G", "octave": 3, "frequency": 196.00},
            {"note": "B", "octave": 3, "frequency": 246.94},
            {"note": "E", "octave": 4, "frequency": 329.63},
        ],
        "freq_range": [65, 400]
    },
    "bass_standard": {
        "name": "Bass Guitar (Standart)",
        "strings": [
            {"note": "E", "octave": 1, "frequency": 41.20},
            {"note": "A", "octave": 1, "frequency": 55.00},
            {"note": "D", "octave": 2, "frequency": 73.42},
            {"note": "G", "octave": 2, "frequency": 98.00},
        ],
        "freq_range": [35, 120]
    },
    "ukulele": {
        "name": "Ukulele",
        "strings": [
            {"note": "G", "octave": 4, "frequency": 392.00},
            {"note": "C", "octave": 4, "frequency": 261.63},
            {"note": "E", "octave": 4, "frequency": 329.63},
            {"note": "A", "octave": 4, "frequency": 440.00},
        ],
        "freq_range": [250, 500]
    },
    "violin": {
        "name": "Violin",
        "strings": [
            {"note": "G", "octave": 3, "frequency": 196.00},
            {"note": "D", "octave": 4, "frequency": 293.66},
            {"note": "A", "octave": 4, "frequency": 440.00},
            {"note": "E", "octave": 5, "frequency": 659.25},
        ],
        "freq_range": [180, 700]
    },
    "vocal": {
        "name": "Vocal",
        "strings": [],
        "freq_range": [80, 1000]
    },
    "chromatic": {
        "name": "chromatic",
        "strings": [],
        "freq_range": [50, 2000]
    }
}


def frequency_to_note(frequency: float) -> dict:
    """Convert frequency to musical note name and cents deviation"""
    if frequency <= 0:
        return {"note": "--", "octave": 0, "cents": 0, "frequency": 0}
    
    semitones = 12 * np.log2(frequency / 440.0)
    nearest_semitone = round(semitones)
    cents = int((semitones - nearest_semitone) * 100)
    
    note_index = (nearest_semitone + 9) % 12
    octave = 4 + (nearest_semitone + 9) // 12
    
    return {
        "note": NOTE_NAMES[note_index],
        "octave": int(octave),
        "cents": cents,
        "frequency": round(frequency, 2)
    }


def find_closest_string(frequency: float, instrument: str) -> Optional[dict]:
    """Find the closest string/note for the given frequency and instrument"""
    profile = INSTRUMENT_PROFILES.get(instrument)
    if not profile or not profile["strings"]:
        return None
    
    closest = None
    min_diff = float('inf')
    
    for string in profile["strings"]:
        diff = abs(frequency - string["frequency"])
        if diff < min_diff:
            min_diff = diff
            closest = string.copy()
            # Calculate cents deviation from target
            if frequency > 0 and string["frequency"] > 0:
                cents_from_target = 1200 * np.log2(frequency / string["frequency"])
                closest["cents_from_target"] = round(cents_from_target)
            else:
                closest["cents_from_target"] = 0
    
    return closest


def get_instrument_profile(instrument_id: str) -> Optional[dict]:
    """Get instrument profile by ID"""
    return INSTRUMENT_PROFILES.get(instrument_id)


def get_all_instruments() -> dict:
    """Get all instrument profiles"""
    return INSTRUMENT_PROFILES

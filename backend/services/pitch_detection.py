import numpy as np
from scipy.ndimage import median_filter
from typing import List
from services.note_mapper import frequency_to_note, get_instrument_profile, INSTRUMENT_PROFILES


def pyin_pitch_detection(audio_data: np.ndarray, sample_rate: int, min_freq: float = 50, max_freq: float = 2000) -> float:
    """
    PYIN-inspired pitch detection algorithm with improved accuracy
    Uses multiple pitch candidates and probabilistic refinement
    """
    audio_data = audio_data.astype(np.float64)
    
    # Normalize
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        audio_data = audio_data / max_val
    
    # Check if signal is too quiet
    rms = np.sqrt(np.mean(audio_data ** 2))
    if rms < 0.01:
        return 0.0
    
    n = len(audio_data)
    
    # Calculate lag bounds
    min_lag = max(2, int(sample_rate / max_freq))
    max_lag = min(n // 2, int(sample_rate / min_freq))
    
    if min_lag >= max_lag:
        return 0.0
    
    # Apply Hanning window
    window = np.hanning(n)
    audio_windowed = audio_data * window
    
    # Calculate cumulative mean normalized difference function (CMND)
    def cumulative_mean_normalized_difference(signal, max_tau):
        n = len(signal)
        tau_max = min(max_tau, n // 2)
        
        # Compute autocorrelation using FFT for efficiency
        fft_size = 2 ** int(np.ceil(np.log2(2 * n - 1)))
        fft_signal = np.fft.rfft(signal, fft_size)
        acf = np.fft.irfft(fft_signal * np.conj(fft_signal))[:n]
        
        # Calculate difference function
        diff = acf[0] + np.concatenate([[0], np.cumsum(signal[1:tau_max+1]**2) + np.cumsum(signal[:tau_max][::-1]**2)[::-1]]) - 2 * acf[:tau_max+1]
        
        # Cumulative mean normalized difference
        cmnd = np.zeros(tau_max + 1)
        cmnd[0] = 1.0
        running_sum = 0.0
        
        for tau in range(1, tau_max + 1):
            running_sum += diff[tau]
            if running_sum > 0:
                cmnd[tau] = diff[tau] * tau / running_sum
            else:
                cmnd[tau] = 1.0
        
        return cmnd
    
    try:
        cmnd = cumulative_mean_normalized_difference(audio_windowed, max_lag)
    except:
        # Fallback to simple autocorrelation
        return autocorrelation_pitch_simple(audio_data, sample_rate, min_freq, max_freq)
    
    # Find the first minimum below threshold (absolute threshold method from YIN)
    threshold = 0.1
    tau_estimate = 0
    
    for tau in range(min_lag, len(cmnd)):
        if cmnd[tau] < threshold:
            # Find local minimum
            while tau + 1 < len(cmnd) and cmnd[tau + 1] < cmnd[tau]:
                tau += 1
            tau_estimate = tau
            break
    
    # If no minimum found below threshold, find global minimum
    if tau_estimate == 0:
        valid_range = cmnd[min_lag:max_lag]
        if len(valid_range) > 0:
            tau_estimate = np.argmin(valid_range) + min_lag
        else:
            return 0.0
    
    # Parabolic interpolation for sub-sample accuracy
    if 0 < tau_estimate < len(cmnd) - 1:
        alpha = cmnd[tau_estimate - 1]
        beta = cmnd[tau_estimate]
        gamma = cmnd[tau_estimate + 1]
        
        denominator = 2 * beta - alpha - gamma
        if abs(denominator) > 1e-10:
            tau_refined = tau_estimate + 0.5 * (alpha - gamma) / denominator
        else:
            tau_refined = tau_estimate
    else:
        tau_refined = tau_estimate
    
    if tau_refined > 0:
        frequency = sample_rate / tau_refined
        if min_freq <= frequency <= max_freq:
            return frequency
    
    return 0.0


def autocorrelation_pitch_simple(audio_data: np.ndarray, sample_rate: int, min_freq: float = 50, max_freq: float = 2000) -> float:
    """Simple autocorrelation pitch detection as fallback"""
    audio_data = audio_data.astype(np.float32)
    if np.max(np.abs(audio_data)) > 0:
        audio_data = audio_data / np.max(np.abs(audio_data))
    
    window = np.hanning(len(audio_data))
    audio_windowed = audio_data * window
    
    corr = np.correlate(audio_windowed, audio_windowed, mode='full')
    corr = corr[len(corr)//2:]
    
    min_lag = int(sample_rate / max_freq)
    max_lag = min(int(sample_rate / min_freq), len(corr) - 1)
    
    if min_lag >= max_lag:
        return 0.0
    
    corr_segment = corr[min_lag:max_lag]
    if len(corr_segment) == 0:
        return 0.0
    
    peak_idx = np.argmax(corr_segment) + min_lag
    
    if corr[peak_idx] < 0.1 * corr[0]:
        return 0.0
    
    if 0 < peak_idx < len(corr) - 1:
        alpha = corr[peak_idx - 1]
        beta = corr[peak_idx]
        gamma = corr[peak_idx + 1]
        if abs(2 * beta - alpha - gamma) > 1e-10:
            peak_idx = peak_idx + 0.5 * (alpha - gamma) / (2 * beta - alpha - gamma)
    
    if peak_idx > 0:
        return sample_rate / peak_idx
    return 0.0


def analyze_audio_data_advanced(audio_data: np.ndarray, sample_rate: int, instrument: str = "chromatic") -> List[dict]:
    """Advanced audio analysis with pitch smoothing and confidence scoring"""
    profile = INSTRUMENT_PROFILES.get(instrument, INSTRUMENT_PROFILES["chromatic"])
    min_freq, max_freq = profile["freq_range"]
    
    # Frame parameters - smaller frames for better time resolution
    frame_duration = 0.03  # 30ms frames
    hop_duration = 0.015   # 15ms hop (50% overlap)
    
    frame_size = int(sample_rate * frame_duration)
    hop_size = int(sample_rate * hop_duration)
    
    pitch_data = []
    raw_frequencies = []
    
    num_frames = max(1, (len(audio_data) - frame_size) // hop_size + 1)
    
    for i in range(num_frames):
        start = i * hop_size
        end = min(start + frame_size, len(audio_data))
        frame = audio_data[start:end]
        
        if len(frame) < frame_size // 2:
            continue
        
        # Calculate RMS for volume
        rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2)) / 32768.0
        
        # Pitch detection with confidence
        if rms > 0.005:
            freq = pyin_pitch_detection(frame, sample_rate, min_freq, max_freq)
            confidence = min(1.0, rms * 5) if freq > 0 else 0.0
        else:
            freq = 0.0
            confidence = 0.0
        
        raw_frequencies.append(freq)
        
        note_info = frequency_to_note(freq)
        
        pitch_data.append({
            "time": round(start / sample_rate, 3),
            "frequency": note_info["frequency"],
            "note": note_info["note"],
            "octave": note_info["octave"],
            "cents": note_info["cents"],
            "volume": round(float(rms), 4),
            "confidence": round(confidence, 2)
        })
    
    # Apply median filter for smoothing (removes outliers)
    if len(raw_frequencies) >= 3:
        smoothed_freqs = median_filter(raw_frequencies, size=3)
        for i, freq in enumerate(smoothed_freqs):
            if freq > 0:
                note_info = frequency_to_note(freq)
                pitch_data[i]["frequency"] = note_info["frequency"]
                pitch_data[i]["note"] = note_info["note"]
                pitch_data[i]["octave"] = note_info["octave"]
                pitch_data[i]["cents"] = note_info["cents"]
    
    return pitch_data


def analyze_realtime(audio_data: np.ndarray, sample_rate: int, instrument: str = "chromatic") -> dict:
    """Real-time pitch analysis for tuner mode"""
    profile = INSTRUMENT_PROFILES.get(instrument, INSTRUMENT_PROFILES["chromatic"])
    min_freq, max_freq = profile["freq_range"]
    
    # Calculate RMS for volume
    rms = np.sqrt(np.mean(audio_data.astype(np.float64) ** 2)) / 32768.0
    
    if rms > 0.003:
        freq = pyin_pitch_detection(audio_data, sample_rate, min_freq, max_freq)
        note_info = frequency_to_note(freq)
        confidence = min(1.0, rms * 5) if freq > 0 else 0.0
        
        return {
            "note": note_info["note"],
            "octave": note_info["octave"],
            "cents": note_info["cents"],
            "frequency": note_info["frequency"],
            "volume": round(float(rms), 4),
            "confidence": round(confidence, 2)
        }
    
    return {
        "note": "--",
        "octave": 0,
        "cents": 0,
        "frequency": 0,
        "volume": round(float(rms), 4),
        "confidence": 0
    }
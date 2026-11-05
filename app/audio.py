"""Controlled audio perturbation and non-learned denoising; no made-up audio benchmarks."""
from __future__ import annotations
import io
import math
import wave
import numpy as np
from scipy import signal

SAMPLE_RATE = 16000
MAX_SECONDS = 30.0


def decode_wav(data: bytes) -> np.ndarray:
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            if wav.getcomptype() != "NONE":
                raise ValueError("Compressed WAV is unsupported; export PCM WAV")
            sr, channels, width, frames = wav.getframerate(), wav.getnchannels(), wav.getsampwidth(), wav.getnframes()
            if sr < 8000 or sr > 96000 or channels not in (1, 2) or width not in (1, 2, 4):
                raise ValueError("Use 8–96 kHz mono/stereo PCM WAV, 8/16/32-bit")
            if not 0.2 <= frames / sr <= MAX_SECONDS:
                raise ValueError("Recording must be between 0.2 and 30 seconds")
            raw = wav.readframes(frames)
            if len(raw) != frames * channels * width:
                raise ValueError("Truncated WAV: audio data does not match declared frame count")
    except (EOFError, wave.Error) as exc:
        raise ValueError("Invalid WAV file") from exc
    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}[width]
    arr = np.frombuffer(raw, dtype=dtype).astype(np.float64)
    arr = ((arr - 128) / 128) if width == 1 else arr / float(2 ** (8*width-1))
    if channels == 2:
        arr = arr.reshape(-1, 2).mean(axis=1)
    if sr != SAMPLE_RATE:
        g = math.gcd(sr, SAMPLE_RATE)
        arr = signal.resample_poly(arr, SAMPLE_RATE // g, sr // g)
    return np.clip(arr, -1.0, 1.0).astype(np.float32)


def encode_wav(audio: np.ndarray, sr: int = SAMPLE_RATE) -> bytes:
    arr = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sr)
        wav.writeframes(arr.tobytes())
    return out.getvalue()


def band_limited(x: np.ndarray, lo: float, hi: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    sos = signal.butter(4, [lo, min(hi, sr*0.48)], btype="bandpass", fs=sr, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def pseudo_ambience(n: int, profile: str, seed: int) -> np.ndarray:
    """Synthetic noise only — NOT authentic recordings of a station/street."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n).astype(np.float32)
    t = np.arange(n, dtype=np.float32) / SAMPLE_RATE
    if profile == "broadband":
        noise = white
    elif profile == "crowd_synthetic":
        noise = band_limited(white, 180, 2600)
        noise += 0.15 * np.sin(2*np.pi*180*t) + 0.1*np.sin(2*np.pi*320*t)
        noise *= (0.65 + 0.35*np.sin(2*np.pi*0.41*t)**2)
    elif profile == "traffic_synthetic":
        noise = 0.85 * band_limited(white, 70, 2800)
        noise += 0.2 * np.sin(2*np.pi*(220+30*np.sin(2*np.pi*0.3*t))*t)
        noise += 0.16 * np.sin(2*np.pi*720*t) * (np.sin(2*np.pi*0.6*t) > 0.65)
    elif profile == "hum_synthetic":
        noise = 0.3 * white + np.sin(2*np.pi*50*t) + 0.15*np.sin(2*np.pi*100*t)
    else:
        raise ValueError("Unknown noise profile")
    return np.asarray(noise, dtype=np.float32)


def mix_snr(speech: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    if len(noise) < len(speech):
        noise = np.tile(noise, math.ceil(len(speech) / max(1, len(noise))))
    noise = noise[:len(speech)].copy()
    speech_rms = np.sqrt(np.mean(speech.astype(np.float64)**2) + 1e-12)
    noise_rms = np.sqrt(np.mean(noise.astype(np.float64)**2) + 1e-12)
    gain = speech_rms / (10**(snr_db/20) * noise_rms)
    combined = speech + noise * gain
    # Avoid clipping by applying a common gain; document peak normalization.
    peak = np.max(np.abs(combined))
    if peak > 0.98:
        combined = combined * (0.98 / peak)
    return combined.astype(np.float32)


def phone_channel(audio: np.ndarray) -> np.ndarray:
    """Synthetic PSTN-like filter+down/up-sampling; not a real phone call."""
    low = band_limited(audio, 300, 3400)
    down = signal.resample_poly(low, 1, 2)
    back = signal.resample_poly(down, 2, 1)
    return back[:len(audio)].astype(np.float32)


def spectral_denoise(audio: np.ndarray, strength: float = 1.1) -> np.ndarray:
    """Stationary noise-floor spectral attenuation; may worsen speech, measure both paths."""
    if len(audio) < 1024:
        return audio.copy()
    _, _, z = signal.stft(audio.astype(np.float64), fs=SAMPLE_RATE, nperseg=512, noverlap=384)
    power = np.abs(z) ** 2
    floor = np.percentile(power, 17, axis=1, keepdims=True)
    gain = np.maximum(0.08, 1 - strength * floor / (power + 1e-12))
    _, rec = signal.istft(z * gain, fs=SAMPLE_RATE, nperseg=512, noverlap=384)
    if len(rec) < len(audio):
        rec = np.pad(rec, (0, len(audio)-len(rec)))
    return np.clip(rec[:len(audio)], -1, 1).astype(np.float32)


def create_variants(audio: np.ndarray, profile: str, snr_db: float, telephony: bool, seed: int, ambience: np.ndarray | None = None) -> dict[str, np.ndarray]:
    clean = audio.copy()
    degraded = audio.copy()
    if profile == "uploaded_ambience":
        if ambience is None or not len(ambience):
            raise ValueError("Upload a WAV field-ambience recording")
        degraded = mix_snr(degraded, ambience, snr_db)
    elif profile != "none":
        degraded = mix_snr(degraded, pseudo_ambience(len(audio), profile, seed), snr_db)
    if telephony:
        degraded = phone_channel(degraded)
    # Recovery here is classical filtering, not corrected transcripts or a new trained model.
    recovered = spectral_denoise(degraded)
    return {"clean": clean, "degraded": degraded, "recovered": recovered}

"""Reference-free acoustic recovery controller. Heuristics are unvalidated on real ASR."""
from __future__ import annotations
import time
import numpy as np
from scipy import signal
from .audio import SAMPLE_RATE, spectral_denoise

POLICY_VERSION = 'acoustic-heuristic-v1'


def analyze(audio: np.ndarray) -> dict:
    x = np.asarray(audio, dtype=np.float64)
    if x.ndim != 1 or not len(x) or len(x) > SAMPLE_RATE * 30 or not np.isfinite(x).all():
        raise ValueError('Expected finite mono audio of at most 30 seconds')
    rms = float(np.sqrt(np.mean(x*x)))
    frames = np.pad(x, (0, (-len(x)) % 320)).reshape(-1, 320)
    energies = np.mean(frames*frames, axis=1)
    floor = float(np.percentile(energies, 20))
    top = float(np.percentile(energies, 90))
    ratio = float(10*np.log10((top+1e-12)/(floor+1e-12)))
    _, _, z = signal.stft(x, fs=SAMPLE_RATE, nperseg=min(512,len(x)))
    power = np.abs(z)**2 + 1e-18
    flatness = float(np.mean(np.exp(np.mean(np.log(power), axis=0))/np.mean(power, axis=0)))
    stationarity = float(np.std(energies)/(np.mean(energies)+1e-12))
    return {'rms': rms, 'clipping_ratio': float(np.mean(np.abs(x)>=.995)),
            'silence_ratio': float(np.mean(energies<1e-6)), 'noise_floor_power_estimate': floor,
            'energy_contrast_db': ratio, 'spectral_flatness': flatness,
            'energy_variation': stationarity,
            'estimate_note': 'Energy contrast is a percentile acoustic heuristic, not measured speech SNR; silence/activity is energy-based, not a validated VAD.'}


def recover(audio: np.ndarray, mode: str = 'adaptive') -> tuple[np.ndarray, dict]:
    if mode not in {'passthrough','fixed','adaptive'}:
        raise ValueError('Recovery mode must be passthrough, fixed or adaptive')
    start = time.perf_counter()
    features = analyze(audio)
    x = np.asarray(audio, dtype=np.float32)
    strength = 0.0
    action, reason = 'passthrough', 'User selected unmodified degraded audio'
    if mode == 'fixed':
        action, strength, reason = 'spectral_attenuation', 1.1, 'Baseline fixed spectral attenuation; may harm speech'
    elif mode == 'adaptive':
        if features['rms'] < .001 or features['silence_ratio'] > .95:
            reason = 'Near-silent signal; filtering cannot recover missing speech'
        elif features['clipping_ratio'] > .01:
            reason = 'Clipping detected; stationary filtering cannot restore clipped samples'
        elif features['energy_contrast_db'] > 20:
            reason = 'Large energy contrast; preserve potentially clean speech to avoid unnecessary filtering'
        elif features['energy_variation'] > 1.5:
            reason = 'Strong energy variation; stationary noise assumption is unreliable'
        elif features['spectral_flatness'] < .015:
            reason = 'Strongly tonal signal; preserve narrowband speech structure'
        else:
            action, strength = 'conservative_spectral_attenuation', .35
            reason = 'Moderate energy variation and broadband content; use bounded conservative attenuation'
    result = spectral_denoise(x,strength=strength) if strength else x.copy()
    distortion = float(np.sqrt(np.mean((result-x).astype(np.float64)**2)))
    if not np.isfinite(result).all() or np.sqrt(np.mean(result.astype(np.float64)**2)) < features['rms']*.25:
        result = x.copy(); action = 'passthrough'; reason = 'Output safety guard rejected excessive attenuation or nonfinite values'; strength=0.0;distortion=0.0
    return result, {'policy_version':POLICY_VERSION,'mode':mode,'action':action,'strength':strength,'reason':reason,
                    'features':features,'processing_seconds':round(time.perf_counter()-start,6),
                    'audio_difference_rms':distortion,'reference_free':True,'validated_asr_improvement':False,
                    'clarification_recommended': features['rms'] < .001 or features['clipping_ratio'] > .01,
                    'clarification_note':'Ask the speaker to repeat/confirm critical information separately; never replace uncertain words automatically.'}

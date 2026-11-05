import io
import wave
import numpy as np
import pytest
from app.audio import decode_wav,encode_wav,mix_snr,phone_channel,spectral_denoise,create_variants

@pytest.fixture
def speech():
    t = np.arange(16000)/16000
    return (0.14*np.sin(2*np.pi*250*t)+0.08*np.sin(2*np.pi*850*t)).astype(np.float32)

def test_wav_roundtrip(speech):
    restored=decode_wav(encode_wav(speech))
    assert len(restored) == len(speech)
    assert abs(restored[100]-speech[100]) < 1e-4

def test_rejects_too_short():
    with pytest.raises(ValueError):decode_wav(encode_wav(np.zeros(50,dtype=np.float32)))

def test_all_variants_keep_length(speech):
    v=create_variants(speech,'traffic_synthetic',8,True,42)
    assert all(len(x)==len(speech) for x in v.values())
    assert not np.allclose(v['clean'],v['degraded'])

def test_seed_reproducible(speech):
    a=create_variants(speech,'crowd_synthetic',4,False,123)
    b=create_variants(speech,'crowd_synthetic',4,False,123)
    assert np.array_equal(a['degraded'],b['degraded'])

def test_denoise_finite(speech):
    assert np.isfinite(spectral_denoise(speech)).all()

def test_field_noise_required(speech):
    with pytest.raises(ValueError):create_variants(speech,'uploaded_ambience',10,False,1)

def test_no_unwanted_volume_explosion(speech):
    noisy=mix_snr(speech,np.ones_like(speech),-5)
    assert max(abs(noisy))<=1.0

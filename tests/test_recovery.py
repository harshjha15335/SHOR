"""Synthetic acoustic software tests, never evidence of improved ASR."""
import inspect
import numpy as np
import pytest
from app.recovery import recover,analyze
from app.audio import spectral_denoise


def noise(seed=1):return np.random.default_rng(seed).normal(0,.05,16000).astype(np.float32)

def tone():return (np.sin(np.arange(16000)*2*np.pi*300/16000)*.1).astype(np.float32)

@pytest.mark.parametrize('mode',['passthrough','fixed','adaptive'])
def test_valid_output(mode):
 x=noise(); y,d=recover(x,mode)
 assert len(y)==len(x)
 assert np.isfinite(y).all()
 assert d['reference_free'] is True
 assert d['validated_asr_improvement'] is False
 assert d['processing_seconds']>=0

def test_passthrough_identity():
 x=noise();y,d=recover(x,'passthrough');assert np.array_equal(x,y);assert d['strength']==0

def test_silent_pass_through():
 x=np.zeros(16000,dtype=np.float32);y,d=recover(x)
 assert np.array_equal(x,y);assert d['action']=='passthrough';assert d['clarification_recommended']

def test_clipped_pass_through():
 x=np.clip(noise()*100,-1,1);y,d=recover(x)
 assert np.array_equal(x,y);assert 'Clipping' in d['reason']

def test_tonal_pass_through():
 x=tone();y,d=recover(x)
 assert np.array_equal(x,y);assert d['action']=='passthrough'

def test_stationary_noise_conservative():
 _,d=recover(noise());assert d['strength']==.35;assert d['action']=='conservative_spectral_attenuation'

def test_nonstationary_preserved():
 x=noise();x[:14000]*=.01
 y,d=recover(x);assert d['action']=='passthrough';assert np.array_equal(x,y)

def test_recovery_may_damage_clean_tonal_signal():
 x=tone();fixed=spectral_denoise(x); adaptive,d=recover(x,'adaptive')
 # A genuine waveform distortion test, not a claimed transcription regression.
 assert np.sqrt(np.mean((fixed-x)**2))>0
 assert np.array_equal(adaptive,x)

def test_strategy_determinism_and_no_reference_surface():
 x=noise();y,a=recover(x);z,b=recover(x)
 assert np.array_equal(y,z)
 assert a['reason']==b['reason'];assert a['features']==b['features']
 assert set(inspect.signature(recover).parameters)=={'audio','mode'}
 with pytest.raises(TypeError):recover(x,reference='answer')

@pytest.mark.parametrize('x',[np.array([]),np.array([np.nan]),np.array([np.inf]),np.zeros((3,3)),np.zeros(480001)])
def test_invalid_input(x):
 with pytest.raises(ValueError):analyze(x)

def test_invalid_mode():
 with pytest.raises(ValueError):recover(noise(),'invalid')

def test_indicators_do_not_claim_measured_snr():
 d=analyze(noise());assert 'not measured speech SNR' in d['estimate_note']
 assert 'snr' not in d

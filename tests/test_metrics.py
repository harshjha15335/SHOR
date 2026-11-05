import pytest
from app.metrics import normalize, edit_distance, score, compare

def test_normalize_preserves_indic_script():
    assert normalize('नमस्ते, दुनिया!') == 'नमस्ते दुनिया'

def test_normalize_latin_case_and_punctuation():
    assert normalize('HELLO, World!') == 'hello world'

def test_wer_known():
    result = score('hello world today', 'hello today')
    assert result['wer'] == 33.33
    assert result['word_edits'] == 1

def test_wer_can_exceed_100_with_insertions():
    assert score('hello', 'hello more more more')['wer'] == 300.0

def test_critical_term_whole_token():
    r = score('send 25 now', 'send 125 now', ['25'])
    assert r['critical_recall'] == 0

def test_critical_term_phrase():
    r = score('call me kal subah', 'call me kal subah', ['kal subah'])
    assert r['critical_recall'] == 100

def test_missing_critical_ref_not_scored():
    assert score('hello world', 'hello world', ['₹500'])['critical_recall'] is None

def test_zero_reference_fails():
    with pytest.raises(ValueError): score('', 'hi')

def test_comparison_no_false_gain():
    assert compare({'wer': 10.0},{'wer': 15.0})['recovery_effect'] == 'worsened'
    assert compare(None,{'wer': 15.0}) is None

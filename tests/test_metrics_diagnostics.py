"""Software-only scoring fixtures; these are not Gnani benchmark results."""
import pytest
from app.metrics import score, align_words, edit_distance

@pytest.mark.parametrize('ref,hyp,counts',[
 ('a b c','a x c',(1,0,0)),('a b c','a c',(0,1,0)),('a b','a x b',(0,0,1)),
 ('a a b','a b',(0,1,0)),('नमस्ते दुनिया','नमस्ते',(0,1,0)),
 ('நாளை காலை','நாளை மாலை',(1,0,0)),('ನಾಳೆ ಕರೆ','ನಾಳೆ ಕರೆ',(0,0,0)),
 ('कल appointment है','कल appointment है',(0,0,0)),('one','',(0,1,0)),
 ('hello','hello x x x',(0,0,3))])
def test_alignment_counts(ref,hyp,counts):
 m=score(ref,hyp)
 assert (m['substitutions'],m['deletions'],m['insertions'])==counts
 assert sum(counts)==m['word_edits']==edit_distance(ref.split(),hyp.split())
 assert [x['reference'] for x in m['alignment'] if x['reference'] is not None]==m['normalized_reference'].split()
 assert [x['hypothesis'] for x in m['alignment'] if x['hypothesis'] is not None]==m['normalized_hypothesis'].split()

def test_deterministic_repeated_alignment():
 assert align_words(['a','a'],['a'])==align_words(['a','a'],['a'])

def test_strict_and_unicode_separate():
 assert score('HELLO, world','hello world')['wer']==0
 assert score('HELLO, world','hello world',scoring_mode='strict')['wer']==50

def test_combining_unicode():
 assert score('café','cafe\u0301')['wer']==0
 assert score('café','cafe\u0301',scoring_mode='strict')['wer']==100

def test_invalid_mode():
 with pytest.raises(ValueError):score('a','a',scoring_mode='transliterate')

def test_number_phrase_eligibility():
 m=score('send 25 kal subah','send 125 kal subah',['25','kal subah','absent','25'])
 assert m['critical_number_accuracy']==0
 assert m['critical_phrase_accuracy']==100
 assert m['critical_recall']==50
 assert len(m['critical_checks'])==3
 assert any(x['critical'] for x in m['alignment'])
 assert any(x['category']=='critical_number_miss' for x in m['failure_taxonomy'])

def test_no_semantic_number_equivalence():
 assert score('twenty five','25',['twenty five'])['critical_phrase_accuracy']==0

def test_script_heuristic_not_diagnosis():
 m=score('नमस्ते','namaste')
 assert m['failure_taxonomy'][-1]['basis']=='heuristic_requires_review'

def test_invalid_reference_and_size():
 with pytest.raises(ValueError):score('!!!','hello')
 with pytest.raises(ValueError):score('a'*10001,'hello')


def test_character_pair_resource_bound():
 with pytest.raises(ValueError, match='four million'):
  score('a'*2001,'a'*2000)
 assert score('a'*2000,'a'*2000)['cer']==0

"""Deterministic script-preserving error analysis; no transliteration or semantic claims."""
from __future__ import annotations
import unicodedata


def normalize(text: str) -> str:
    s = unicodedata.normalize('NFKC', text).casefold()
    return ' '.join(''.join(' ' if unicodedata.category(c)[0] in {'P', 'S'} else c for c in s).split())


def edit_distance(a: list[str] | str, b: list[str] | str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, c in enumerate(a, 1):
        current = [i]
        for j, d in enumerate(b, 1):
            current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (c != d)))
        previous = current
    return previous[-1]


def align_words(reference: list[str], hypothesis: list[str]) -> list[dict]:
    """Levenshtein backtrace; ties prefer diagonal, then deletion, then insertion."""
    if len(reference) * len(hypothesis) > 1_000_000:
        raise ValueError('Transcript alignment exceeds one million token pairs')
    d = [list(range(len(hypothesis) + 1))]
    for i, a in enumerate(reference, 1):
        row = [i]
        for j, b in enumerate(hypothesis, 1):
            row.append(min(d[i-1][j] + 1, row[-1] + 1, d[i-1][j-1] + (a != b)))
        d.append(row)
    i, j = len(reference), len(hypothesis)
    out = []
    while i or j:
        if i and j and d[i][j] == d[i-1][j-1] + (reference[i-1] != hypothesis[j-1]):
            i -= 1; j -= 1
            out.append({'operation': 'correct' if reference[i] == hypothesis[j] else 'substitution',
                        'reference': reference[i], 'hypothesis': hypothesis[j], 'reference_index': i, 'hypothesis_index': j})
        elif i and d[i][j] == d[i-1][j] + 1:
            i -= 1
            out.append({'operation': 'deletion', 'reference': reference[i], 'hypothesis': None, 'reference_index': i, 'hypothesis_index': None})
        else:
            j -= 1
            out.append({'operation': 'insertion', 'reference': None, 'hypothesis': hypothesis[j], 'reference_index': None, 'hypothesis_index': j})
    return out[::-1]


def _contains(seq, needle):
    return bool(needle) and any(seq[i:i+len(needle)] == needle for i in range(len(seq)-len(needle)+1))


def _recall(checks):
    eligible = [c for c in checks if c['in_reference']]
    return round(100 * sum(c['preserved'] for c in eligible) / len(eligible), 2) if eligible else None


def score(reference: str, hypothesis: str, critical_terms: list[str] | None = None, scoring_mode: str = 'unicode') -> dict:
    if scoring_mode not in {'strict', 'unicode'}:
        raise ValueError('scoring_mode must be strict or unicode; transliteration is not validated')
    if len(reference) > 10000 or len(hypothesis) > 10000:
        raise ValueError('Transcripts must not exceed 10000 characters')
    transform = normalize if scoring_mode == 'unicode' else lambda x: ' '.join(x.split())
    r, h = transform(reference), transform(hypothesis)
    rw, hw = r.split(), h.split()
    if not rw:
        raise ValueError('Reference transcript must contain actual spoken words')
    alignment = align_words(rw, hw)
    counts = {op: sum(x['operation'] == op for x in alignment) for op in ('correct', 'substitution', 'deletion', 'insertion')}
    w_edits = counts['substitution'] + counts['deletion'] + counts['insertion']
    r_chars, h_chars = r.replace(' ', ''), h.replace(' ', '')
    if len(r_chars) * len(h_chars) > 4_000_000:
        raise ValueError('Character scoring exceeds four million character pairs')
    c_edits = edit_distance(r_chars, h_chars)
    checks = []
    for term in dict.fromkeys(t.strip() for t in (critical_terms or []) if t.strip()):
        words = transform(term).split()
        checks.append({'term': term, 'in_reference': _contains(rw, words), 'preserved': _contains(hw, words),
                       'kind': 'number' if any(c.isdecimal() for c in term) else 'phrase' if len(words) > 1 else 'token'})
    for entry in alignment:
        token = entry['reference'] or entry['hypothesis']
        entry['critical'] = any(token in transform(c['term']).split() for c in checks if c['in_reference'])
    taxonomy = []
    for op in ('substitution', 'deletion', 'insertion'):
        if counts[op]: taxonomy.append({'category': op, 'basis': 'measured_alignment', 'count': counts[op]})
    if not hw: taxonomy.append({'category': 'empty_output', 'basis': 'measured', 'count': 1})
    if any(c['kind'] == 'number' and c['in_reference'] and not c['preserved'] for c in checks):
        taxonomy.append({'category': 'critical_number_miss', 'basis': 'exact_token_check', 'count': sum(c['kind'] == 'number' and c['in_reference'] and not c['preserved'] for c in checks)})
    # Different scripts are a review prompt, not proof of recognition failure.
    def scripts(s):
        return {unicodedata.name(c, '').split()[0] for c in s if c.isalpha()}
    if scripts(r) and scripts(h) and scripts(r).isdisjoint(scripts(h)):
        taxonomy.append({'category': 'possible_script_mismatch', 'basis': 'heuristic_requires_review', 'count': 1})
    return {'wer': round(100*w_edits/len(rw), 2), 'cer': round(100*c_edits/max(1,len(r_chars)), 2),
            'word_edits': w_edits, 'reference_words': len(rw), 'character_edits': c_edits, 'reference_characters': len(r_chars),
            'substitutions': counts['substitution'], 'deletions': counts['deletion'], 'insertions': counts['insertion'], 'correct_words': counts['correct'],
            'alignment': alignment, 'critical_recall': _recall(checks), 'critical_checks': checks,
            'critical_number_accuracy': _recall([c for c in checks if c['kind'] == 'number']),
            'critical_phrase_accuracy': _recall([c for c in checks if c['kind'] == 'phrase']),
            'failure_taxonomy': taxonomy, 'scoring_mode': scoring_mode,
            'normalized_reference': r, 'normalized_hypothesis': h,
            'normalization_note': ('Unicode NFKC + casefold + punctuation stripping; no cross-script transliteration.' if scoring_mode == 'unicode' else 'Strict script, case and punctuation; whitespace tokenized. No transliteration.'),
            'critical_method': 'Exact eligible term retention; not semantic correctness. Number words and digits are not equated.'}


def compare(degraded: dict | None, recovered: dict | None) -> dict | None:
    if not degraded or not recovered:
        return None
    gain = round(degraded['wer'] - recovered['wer'], 2)
    return {'wer_change_percentage_points': gain,
            'relative_wer_reduction_percent': round(100*gain/degraded['wer'],2) if degraded['wer'] else None,
            'recovery_effect': 'improved' if gain > 0 else 'unchanged' if gain == 0 else 'worsened',
            'interpretation': 'Positive change means lower WER after audio processing; this is not a claim of model retraining.'}

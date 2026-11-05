"""Deterministic, Unicode-aware ASR metrics. No model/quality claims are fabricated."""
from __future__ import annotations
import unicodedata


def normalize(text: str) -> str:
    """Normalize for consistent WER: preserve Indic combining marks, remove punctuation."""
    s = unicodedata.normalize("NFKC", text).casefold()
    cleaned = "".join(" " if unicodedata.category(c)[0] in {"P", "S"} else c for c in s)
    return " ".join(cleaned.split())


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


def score(reference: str, hypothesis: str, critical_terms: list[str] | None = None) -> dict:
    r = normalize(reference)
    h = normalize(hypothesis)
    rw, hw = r.split(), h.split()
    if not rw:
        raise ValueError("Reference transcript must contain actual spoken words")
    w_edits = edit_distance(rw, hw)
    r_chars, h_chars = r.replace(" ", ""), h.replace(" ", "")
    c_edits = edit_distance(r_chars, h_chars)
    terms = [t.strip() for t in (critical_terms or []) if t.strip()]
    checks = []
    for term in terms:
        words = normalize(term).split()
        # Exact token/phrase match: never match '25' inside '125'.
        def contains(seq, needle):
            return bool(needle) and any(seq[i:i+len(needle)] == needle for i in range(len(seq) - len(needle) + 1))
        checks.append({"term": term, "in_reference": contains(rw, words), "preserved": contains(hw, words)})
    eligible = [x for x in checks if x["in_reference"]]
    recall = round(100 * sum(x["preserved"] for x in eligible) / len(eligible), 2) if eligible else None
    return {
        "wer": round(100 * w_edits / len(rw), 2), "cer": round(100 * c_edits / max(1, len(r_chars)), 2),
        "word_edits": w_edits, "reference_words": len(rw), "character_edits": c_edits,
        "reference_characters": len(r_chars), "critical_recall": recall, "critical_checks": checks,
        "normalization_note": "Unicode NFKC + casefold + punctuation stripping; no cross-script transliteration."
    }


def compare(degraded: dict | None, recovered: dict | None) -> dict | None:
    if not degraded or not recovered:
        return None
    gain = round(degraded["wer"] - recovered["wer"], 2)
    return {
        "wer_change_percentage_points": gain,
        "recovery_effect": "improved" if gain > 0 else "unchanged" if gain == 0 else "worsened",
        "interpretation": "Positive change means lower WER after audio processing; this is not a claim of model retraining."
    }

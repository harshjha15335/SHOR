# SHOR research and evaluation method

## Present evidence boundary

The new modules make controlled evaluation possible. They do not establish any
real ASR improvement. No consenting-speaker corpus, genuine provider transcript,
held-out result or statistically significant gain is claimed. Test fixtures and
synthetic tones validate software only. See `evidence/RESULTS.md` for actual
experiment status and `evidence/API_validation.md` for integration blockers.

## Reference-free recovery

`app/recovery.py` accepts only audio and a recovery mode. It does not accept the
reference transcript, recognized text, critical answer, speaker identity or
held-out scores. Its decision is made before transcription/scoring.

- **Pass-through** preserves the degraded signal.
- **Fixed** reproduces the baseline spectral attenuation at strength 1.1.
- **Adaptive** applies a deterministic, bounded heuristic policy. It estimates
  RMS energy, clipping, energy-based silence fraction, percentile energy contrast,
  spectral flatness and energy variation. It falls back to pass-through for
  near-silence, clipping, large energy contrast, strongly variable or strongly
  tonal content; otherwise it uses conservative attenuation at strength 0.35.
- An output guard rejects nonfinite/excessively attenuated output. The recorded
  decision includes policy version, action, reason, features, processing time and
  waveform RMS difference. Difference is a distortion indicator, not perceptual
  quality or intelligibility evidence.

These thresholds are **untuned engineering heuristics**, not parameters learned
on a real development dataset. Percentile energy contrast is not measured speech
SNR. Energy activity is not a validated VAD. Conservative filtering may still
remove useful phonetic information or harm recognition. An unchanged signal is
not a failed experiment; avoiding harmful filtering is a legitimate candidate.

A clarification recommendation requests a separate human repeat/confirmation.
The application never silently fills uncertain words from gold text. It does not
implement a live conversational re-ask agent or score a new utterance as if it
were the original fixed-audio intervention.

## Dataset collection and splits

Start with the header-only `evidence/dataset_manifest.csv` and its data dictionary.
Collect nonsensitive, consented Hindi/Hinglish and Tamil/Tanglish speech; prioritize
multiple accents and at least three speakers/20 utterances if achievable. Report
actual counts even when smaller. Do not create fictional rows to meet targets.
Keep filled private manifests and source audio outside public Git history.

Label quiet real, noisy real and legally consented actual telephone recordings
separately from synthetic mixtures and simulated telephone bandwidth. Uploaded
ambient recordings do not turn a mixed synthetic experiment into an actual call.
The original speech and every derivative share a source-utterance identity.

Use approximately 60% development, 20% validation and 20% held-out data where
practical. Freeze the held-out manifest and hashes before tuning. Prevent source
utterances, identical-file hashes and near-duplicate variants crossing splits.
The manifest validator detects declared identities and exact hash leakage; it
cannot detect every acoustically similar near duplicate. Prefer speaker-disjoint
splits and report overlap warnings and small-cohort limitations.

## Reference transcript and critical facts

Transcribe what was spoken, before viewing model output. Keep the original raw
reference; record script convention, reviewer status, disagreements and any
adjudication. A later correction must be versioned and justified rather than
rewritten to favor a model. Predeclare task-relevant amounts, times, identifiers,
negations, names and phrases. Do not send held-out answer text as model keyterms.

## Scoring modes

- `strict`: preserve case, punctuation and script; tokenize whitespace, retaining
  raw spelling. Whitespace is collapsed for tokenization.
- `unicode`: NFKC normalization, casefolding and punctuation/symbol stripping;
  preserve Indic combining marks and script. Do not silently transliterate.
- Validated transliteration/semantic equivalence is **not implemented**. Digit
  `15`, Latin `fifteen` and native-script number words are not automatically equal.

Both modes retain raw reference and returned transcript. Word alignment uses
Levenshtein dynamic programming with deterministic diagonal/deletion/insertion
tie ordering. Labels distinguish correct, substituted, deleted and inserted words.
WER can exceed 100% because of insertions. CER counts code points after the
selected normalization and whitespace removal, not phonemes or grapheme clusters.

Critical-number, phrase and token recall use exact matches, with terms eligible
only when present in the reference. A term containing decimal digits is labeled
a number; spelled-out amounts require explicit terms and human interpretation.
A high WER score cannot establish that an error was caused by noise, and a low
WER cannot make a missed critical fact harmless. Automatic alignment categories
are distinguished from heuristic script-mismatch review prompts. Named-entity,
code-switch causation and reference disagreement need human review.

## Controlled comparisons

The web workbench submits clean/degraded/recovered for one selected recovery mode.
The research runner submits clean/degraded/fixed/adaptive for each chosen model,
using the same source/configuration and recorded hashes. Keep model, language,
format, seed, noise profile, telephone simulation, scoring mode and policy version
fixed and visible. Model selectors do not prove entitlement or comparative quality.
Context/keyterm assistance is not implemented and must be a separately labeled
condition if added later.

Use actual returned model, request ID and provider timing only when available;
missing values remain null. Record requested model separately. Preserve failed,
empty and partial results; a failed request is not an accuracy of zero. Never
choose an inference output by its reference score. Do not tune policy thresholds
on the final held-out cohort.

## Aggregation and interpretation

Corpus WER = 100 × sum(word edits) / sum(reference words). Corpus CER uses the
corresponding character counts. Macro per-sample WER is separately named. Compare
recovery only on matched sample/model pairs; report improved, unchanged and
worsened counts, absolute percentage-point change and relative change only when
the baseline is nonzero. Use group summaries for model, language, condition,
speaker, split and variant rather than pooling unrelated conditions into a claim.

Wall time and provider-reported time are different fields. Acoustic processing
time is not REST latency. The summary withholds p50 below five observations and
p95 below twenty; small observed percentiles still carry sampling limitations.
No confidence interval or significance claim is implemented. Report missing
metrics and request failures alongside denominators and preserve failure cases.
Regenerate summaries from recorded JSONL with `scripts/summarize_evidence.py`;
this makes no fresh API calls and consumes no inference credits.

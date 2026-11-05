# Evaluation protocol v1

## Collection and annotation

Target 20 real utterances across at least 3 consenting speakers, prioritizing Hindi/Hinglish and Tamil/Tanglish. This is a target, not an achieved count. Capture quiet indoor, traffic, crowd, background conversations, fan and poor placement conditions where feasible. Actual consented phone audio is a separate condition; filtering a WAV is not PSTN evidence. Use fictional task details only; no Aadhaar, private phone numbers, customer or medical data.

Get explicit speaker consent for local evaluation and separately for any sharing. Keep consent identities outside the repository. Do not upload recordings until consent and privacy review are complete.

Review references before observing model output. Preserve spoken hesitations and code-switches under a written transcription convention. Record raw reference, reviewer disagreements and adjudication; do not fix the reference to improve a model score. Select critical amounts, times, names, negations and identifiers before model evaluation.

## Dataset split and leakage

Allocate approximately 60/20/20 development/validation/heldout, preferably speaker-disjoint. Freeze heldout before recovery tuning. Assign all exact duplicates and derived versions of a source utterance to one split; the validator checks source IDs and byte hashes. Review near-duplicates manually because hashes cannot detect re-encoding or paraphrases. Speaker overlap is reported, not silently treated as speaker-disjoint. Report exact sample/speaker/word counts and limitations if the small corpus prevents the target split.

## Controls and analysis

Compare degraded audio, fixed spectral attenuation and the reference-free adaptive controller on identical source conditions, with clean as an additional reference arm. Never provide gold transcripts to the recovery controller. Keep inference-time parameters independent from heldout answers. No keyterm/context assistance is used in the current runner.

Use paired v2.5/v3.0 only when actual account entitlement and call budget allow. Do not conclude superiority from one sentence. Preserve every failure and regression. Distinguish acoustic recovery from an interaction intervention: asking for confirmation creates a different measurement, not a silently corrected transcript.

Corpus WER is sum(word_edits)/sum(reference_words), not mean sentence WER. Report macro separately. Group by variant/model/language/condition/speaker/split. Overall summaries pool variants and models and therefore are descriptive counts, not primary scientific comparisons. Paired recovery summaries use matched degraded/recovery samples. No statistical significance or confidence interval is claimed by this small-sample tooling. p50 is exposed only from 5 timings; p95 from 20. Wall time includes client/network overhead, not streaming latency.

Strict versus normalized script comparisons must remain separate experimental conventions. Do not silently transliterate digits, number words, Hindi or Tamil. Exact critical term recall is not semantic correctness.

## Cost and failure policy

Validate the entire manifest before any paid call. Dry-run executes preprocessing but sends zero requests. Initial smoke is one reviewed actual speech sample and one call. Further comparison needs explicit budget approval. The batch runner makes four requests per sample per model with no retries. Output paths must be fresh; per-request JSONL is flushed progressively. Partial failures produce a nonzero exit while preserving successful and failed records. Never pass test doubles off as live evidence.

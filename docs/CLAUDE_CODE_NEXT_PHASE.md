# Claude Code implementation directive: Make SHOR//LAB award-ready

You are taking over the original SHOR//LAB repository. Inspect the entire repository and tests before changing anything. Do **not** rebuild the product from scratch, silently replace the working UI, or copy source from Kasauti. The target competition is the Great Indian AI Internship Challenge, with a November 10, 2026 deadline and the **Noise Canceller Award** as the primary technical category.

## Baseline

- Fully working **local MVP** using FastAPI and a static responsive UI; single WAV upload/mic record, deterministic noise and simulated PSTN filtering, spectral denoising, real Gnani Prisma REST adapter, WER/CER, critical-term exact-match recall, SQLite history and CSV export, a manifest-driven batch benchmarker.
- Never manufacture measured metrics, pretend synthetic noise is genuine telephony, or claim real API tests without a verified Gnani key and actual request IDs.
- No API key is stored in client code. Audio/transcripts are held locally; no public deployment until authentication, retention/deletion and privacy controls exist.
- The model has publicly documented endpoints: `POST https://api.vachana.ai/stt/v3`, API header `X-API-Key-ID`, multipart `audio_file`, `model`, `language_code`, `format=verbatim`; v2.5 and v3.0, v3 `indic-auto`.
- Start with `python -m pytest -q` and pass every existing test.

## Phase A — Validate the baseline

1. Inspect runtime, setup, dependencies, APIs, JS, and tests. Run the app locally.
2. Check WAV input constraints (≤30sec), malformed audio, recordings, Unicode, data retention, duplicate runs, and API failure handling.
3. Fix actual issues; include regression tests. Do not claim untested streaming or sub-200ms latency from REST calls.
4. Run a **real** end-to-end sample with programme credits only after user has set `GNANI_API_KEY` locally. Keep secrets out of logs.

## Phase B — Research-grade failure analysis

1. Implement word alignment/backtrace for substitution/deletion/insertion, including code-mixed Unicode rendering. Display an error diff next to the raw output.
2. Critical phrase / number accuracy must be measured separately, not confused with 1-WER. Choose benchmark targets **before** results.
3. Add a clearly labeled *paired results panel* for degraded vs recovered; score by reference, but NEVER use that gold reference to select outputs during inference.
4. Add model v2.5 vs v3.0 paired comparisons (if supported by participant account), capturing model+format, input SHA-256, request IDs, timing, and exact audio condition.
5. Add an honest error taxonomy: numbers, names, script mismatch, omissions, code switches, human annotation disagreement.

## Phase C — Adaptive recovery (original contribution)

1. Replace naive always-on spectral-gating with a **reference-free decision rule** developed on a training/dev set; it may use acoustic estimates, model-reported signals if actually available, or contextual uncertainty, but cannot look at gold text.
2. Compare at least two recovery strategies (e.g. conservative spectral filtering vs re-ask/human confirmation on critical terms). Measure when each hurts, and show those failures.
3. Carry dev vs held-out split, samples and codebook in the evidence. Never optimize on final held-out clips.
4. Implement privacy-aware data removal and an exportable experiment manifest.

## Phase D — Real audio, review and demo

1. Get consented recordings from speakers and a small **actual noisy environment / actual phone call** set; separate these clearly from synthetic noise mixtures. No real sensitive customer recordings.
2. Capture Indian multilingual speech with 20+ varied utterances across speakers, environments and languages; document limitations and use clear denominators. If the data is smaller, disclose it.
3. Evidence report: per-sample input label, reference, returned transcript, WER/CER, critical-term misses, real request ID, audio hash, environment, model version, aggregate weighted WER, improvement percentage points, p50/p95 wall time, and failure cases. Never cherry-pick only wins.
4. 60-second real screen-capture demo: show source audio, listen to noisy recording, inspect original failed transcript, apply recovery, inspect resulting actual Gnani transcript, display measured delta. If recovery does not improve on a sample, select a *genuinely improved* sample and disclose the broader aggregate.
5. Write an honest technical README, reproducible evaluation instructions, licensing and attribution. Clearly credit original Kasauti as conceptual inspiration without copying it.

## Competition constraints

- At least one **actual Gnani model/API** must be used (not simply the brand in text).
- Gnani agent builder APIs are outside the internship programme's model/credit scope.
- Public LinkedIn and/or X demo post with `#GnaniAI` and `#GreatIndianAIInternshipChallenge` live before the final form submission.
- Do not buy or exchange engagement; do not invent users, benchmarks, testimonials, calls, or evaluation results.
- Submit by **November 10, 2026 at 11:59 PM IST**.

## Output contract

Return: changes to code; tests run and exact results; actual Gnani API evidence (only if a live run took place); measured strengths and weaknesses; run/deployment steps; list of remaining blockers. All features should be testable without assuming undocumented API methods.

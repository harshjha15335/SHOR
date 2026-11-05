# SHOR evidence workspace

No real speech dataset or live API result is included. The CSV contains a header only. Software fixtures in tests are not real participants, consent, or research measurements.

1. Collect consented, nonsensitive recordings using `evaluation_protocol.md`.
2. Fill `dataset_manifest.csv` with reviewed references and SHA-256 values. Keep private manifests outside Git (the committed file is an empty template).
3. Validate and exercise local processing:
   `python scripts/batch_benchmark.py --manifest /private/manifest.csv --dry-run --limit 20`
4. Once runtime credentials, network access and one-call authorization are available:
   `python scripts/live_smoke.py --manifest /private/manifest.csv --sample-id ID --allow-one-live-call --output evidence/raw_results/smoke.jsonl`
5. A full comparison sends **four calls per sample per model** (clean, degraded, fixed, adaptive). Obtain the corresponding credit approval first; no retry is automatic:
   `python scripts/batch_benchmark.py --manifest /private/manifest.csv --models prisma-v2.5 prisma-v3.0 --limit 1 --allow-live --max-api-calls 8 --output evidence/raw_results/paired.jsonl`
6. Regenerate summaries from raw evidence without new API requests:
   `python scripts/summarize_evidence.py evidence/raw_results/paired.jsonl --output evidence/aggregate_results/paired.json`

The original web workflow still uses three variant requests. This research runner explicitly adds a fixed-versus-adaptive comparison and therefore uses four. Context/keyterm-assisted recognition is not implemented and must not be represented as the same condition as audio-only recognition.

Raw transcripts, audio and generated aggregates are ignored locally. Ignoring does not anonymize files or protect manually shared evidence. Review before publication. Do not commit filled private manifests, audio or user data. Outputs are never overwritten by live runners.

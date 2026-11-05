# Dataset manifest dictionary

Every required header appears in `dataset_manifest.csv`; there are no completed samples.

- `sample_id`: unique pseudonymous sample identifier.
- `audio_path`: WAV path relative to the manifest. Private local paths are resolved only on the host.
- `speaker_id`: pseudonym, not name or contact details.
- `language`: supported API language code; Hinglish is annotated using code_mixed and a consistent script convention, not an invented API language.
- `code_mixed`: true/false.
- `recording_environment`: quiet indoor, traffic, fan, etc., based on observed collection conditions.
- `audio_condition`: descriptive condition label used for grouping.
- `actual_or_synthetic_condition`: actual or synthetic. All added noise mixtures (including uploaded ambience) and telephone simulation must be synthetic.
- `recording_device_category`: phone mic, headset, recorder, etc.; avoid device identifiers.
- `original_sample_rate`: checked against WAV header.
- `processed_sample_rate`: 16000.
- `duration_seconds`: decoded duration, checked within 0.02 s.
- `consent_status`: must be consented; retain separate consent records privately.
- `reference_transcript`: exact manually reviewed speech text, not an expected prompt.
- `transcript_script_convention`: native script, mixed script or explicitly documented Romanization policy.
- `critical_terms`: predeclared exact tokens/phrases separated by |. No semantic number equivalence assumed.
- `dataset_split`: development, validation, heldout.
- `file_sha256`: exact source bytes SHA-256; validation recomputes it.
- `noise_profile`: none, broadband, crowd_synthetic, traffic_synthetic, hum_synthetic or uploaded_ambience.
- `configured_snr_db`: finite -5..30 dB; full-signal configured mixture target, not measured active speech SNR.
- `telephone_simulation`: true/false; not proof of actual telephony.
- `processing_seed`: integer 0..10000000.
- `source_utterance_id`: stable family ID across derived variants. Cannot cross splits.
- `reference_review_status`: reviewed required; document reviewer disagreement privately.
- `ambience_path`, `ambience_sha256`: required only for uploaded_ambience; provenance remains a mixture, not a real call.

Runner results preserve experiment ID, sample and speaker pseudonym, split, condition, requested model/language/format, source hash, submitted-variant hash, recovery decision, actual provider transcript/request ID/model where returned, metrics and request timestamps. Missing provider fields stay absent/null. Errors are retained. No provider response or metric is fabricated.

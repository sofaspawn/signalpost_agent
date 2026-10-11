# Signalpost Agent — Norwegian company facts with evidence

Signalpost looks up a Norwegian organization number in Brønnøysundregistrene (BRREG) and returns current official company facts with source links and dates. It aims to make every claim auditable and avoids publishing inferred, stale-cache, or synthetic facts.

The repository also includes `data/brreg_profiles.json`, a dated snapshot of 1,000 real company records fetched from BRREG. The interactive lookup is live and independent of that snapshot; it never silently uses the snapshot as a fallback when BRREG is unavailable.

## Quick start

Python 3.8+, no dependencies:

```bash
python3 agent.py 923609016
```

Returns JSON. A successful lookup makes up to three BRREG requests. Invalid numbers are rejected before network access. See [`QUICKSTART.md`](QUICKSTART.md) for setup, dataset refresh, output details, safeguards, tests, costs, and submission notes.

## Dataset

Refresh the committed 1,000-profile snapshot from the repository root:

```bash
python3 sync_dataset.py
```

The importer verifies each organization number and company name, excludes bulk email/mobile fields, and atomically writes the output only after it has collected the requested minimum. Default output is `data/brreg_profiles.json`; default count is 1,000. Refresh as needed before submission to keep the snapshot current. It is a snapshot, not a live mirror.

## Tests

```bash
python3 -m unittest -v
```

Tests are offline and mock BRREG responses. For full usage and data limitations, read [`QUICKSTART.md`](QUICKSTART.md).

## Safeguards

- Mod-11 validation before lookup.
- Returned BRREG organization number must match the requested number.
- Per-fact source endpoint; unknown update dates remain unknown.
- Source outage, 404, sparse source record, and identity mismatch are distinct.
- Financial values are only emitted from the official accounts response for that organization number.
- No LLM, synthetic profiles, or fabricated financial data.

## Hackathon run details

- One command: `python3 agent.py <company_number>`
- Model: none; Python standard library only.
- API: public BRREG endpoints; no API key.
- Declared external model/API cost: $0 per lookup.
- Up to three outbound requests per successful lookup; the included snapshot is separate from live lookups.

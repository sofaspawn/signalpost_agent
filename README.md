# Signalpost Agent — Norwegian company facts with evidence

Look up a Norwegian organization number against Brønnøysundregistrene (BRREG) and return verified facts with the exact public API record used, source dates where available, source availability, and explicit limitations.

## Run

```bash
python3 agent.py 923609016
```

Python 3.8+; no third-party dependencies. Successful lookups make up to three BRREG requests (company, roles, accounts). The company identity must match the requested number or the profile is withheld. Missing data is omitted; source errors are distinguished from a genuine 404. This tool does not use an LLM and does not infer facts from synthetic data.

Output is JSON. Each fact includes `source`, `source_url`, and `date` (null if BRREG does not provide a defensible fact date). `source_status` describes partial source failures. `data_freshness` distinguishes query date, company record date, and latest accounts period end.

## Tests

```bash
python3 -m unittest -v test_agent.py
```

Tests are offline and mock BRREG responses. A live smoke test, if desired, is `python3 agent.py 923609016`; it requires network access and sends requests to the public BRREG APIs.

## Sources and safeguards

- BRREG Enhetsregisteret: `https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}`
- BRREG roles: `https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}/roller`
- BRREG filed accounts: `https://data.brreg.no/regnskapsregisteret/regnskap/{org_number}`
- Organization numbers are checked for length, allowed leading digit, and Mod-11 check digit before any request.
- A mismatched company number, empty primary record, invalid financial amount, or upstream outage cannot silently become a published fact.
- BRREG does not expose a per-field modification date for every field. In that case the fact date is null; query time is never substituted as a fact update date.
- Financial amounts are included only when present in the filed-accounts response, with the accounts period end attached.

## Coverage and profile count

This is a live lookup agent, not a preloaded set of 1,000 profiles. It can look up companies present in BRREG, including companies not known in advance. The former `company_database.json` contained synthetic values and is intentionally excluded from the agent and submission; it was removed to prevent invented data from being mistaken for real company facts. There is no persistent cache, and no claim is made that a static 1,000-profile dataset is bundled.

## Hackathon details

- One command: `python3 agent.py <company_number>`
- Model: none; deterministic Python standard library implementation.
- External API: public BRREG endpoints; no API key.
- Declared API cost: $0 per lookup (network/provider charges, if any, are outside the software; up to three requests per company).
- No profile data is persisted locally.

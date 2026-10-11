# Signalpost Hackathon Submission

## Repository

https://github.com/sofaspawn/signalpost_agent

## Exact commit hash

**Pending final commit.** After committing the submission-ready changes, run `git rev-parse HEAD` and put that complete hash here. Do not submit the prior repository HEAD; it does not include these changes.

## One command to run

```bash
python3 agent.py <company_number>
```

Example: `python3 agent.py 923609016`

## Profiles

`data/brreg_profiles.json` contains 1,000 real company records collected from the public BRREG Enhetsregister. It is a timestamped snapshot with source URLs, not synthetic data. Refresh with `python3 sync_dataset.py`. The importer validates organization numbers, excludes bulk contact email/mobile fields, and will not overwrite the previous snapshot unless it successfully collects at least the requested number of records.

The CLI fetches each requested company live from BRREG; it does not treat a stale snapshot as current data. It uses the register, roles, and accounts endpoints and binds returned data to the requested organization number before publishing facts.

## Model/API details

No model/LLM is used. Implementation uses the Python standard library. Public unauthenticated BRREG APIs are queried; no API key is required. Up to three outbound requests per successful company lookup. The default dataset refresh obtains 1,000 profiles with one search request (more only if pagination is needed).

## Expected run costs

$0 in declared model/API costs per lookup. No paid model or API is called. Network/provider charges, if any, are outside the program's declared external API cost.

## Evidence and safety

Each emitted fact contains its source endpoint and a source date where one is known. Unknown fact dates are null; query time is not presented as a fact update date. Invalid identifiers are rejected; identity mismatches, source outages, and 404s are handled distinctly. Financial values are only published from the requested organization's filed-accounts response. The bundled company snapshot excludes bulk email/mobile fields.

## Validation

```bash
python3 -m unittest -v
python3 -m py_compile agent.py sync_dataset.py test_agent.py
```

The unit tests are offline. The live example lookup requires network access to BRREG.

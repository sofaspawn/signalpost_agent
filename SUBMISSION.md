# Signalpost Hackathon Submission

## Repository

Update with the public repository URL before submission.

## Commit hash

Use `git rev-parse HEAD` at the final submission commit; do not reuse a stale hash from an earlier revision.

## One command to run

```bash
python3 agent.py <company_number>
```

Example: `python3 agent.py 923609016`

## Model and API details

No LLM or external model is used. The agent is implemented in Python standard library and queries the public BRREG Enhetsregisteret, roles, and filed-accounts APIs. No API key is required. Requests are made only for the supplied organization number; up to three outbound API requests per lookup.

## Expected run costs

$0 in declared model/API charges per lookup. BRREG API access is public and unauthenticated. No LLM or paid API is called. Up to three outbound requests are made for a successful company profile.

## Data and safety

Results are retrieved live, not from a preloaded 1,000-profile dataset. Organization numbers are validated before querying. A response with the wrong organization number is rejected. Facts carry their BRREG endpoint and source date when available; an unknown date is `null`. Upstream failure is distinct from a verified 404. Financial values are published only when present in the official accounts response. The previous synthetic `company_database.json` was removed because it contained invented values and must not be used as company evidence.

## Qualification caveat

The project currently does **not** bundle at least 1,000 real company profiles. Live BRREG lookup supports broad coverage but should not be represented as satisfying a static-profile-count requirement unless the organizers confirm that live retrieval qualifies. Verify this with the challenge rules before submission.

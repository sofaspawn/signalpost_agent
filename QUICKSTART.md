# Quick start

Requires Python 3.8+; no dependencies to install.

```bash
python3 agent.py 923609016
```

The command returns JSON from live BRREG public APIs. Successful lookups request company details, roles, and filed accounts. It needs network access. If BRREG cannot verify the requested company, the agent reports a structured error rather than returning a synthetic profile.

## Run the offline regression suite

```bash
python3 -m unittest -v test_agent.py
```

The tests cover organization-number checksum validation, identity mismatch rejection, per-fact evidence links, missing dates, annual-account values, partial outages, and 404 handling. For endpoint details and limitations, see `README.md`.

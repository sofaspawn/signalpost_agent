# Signalpost — Norwegian company intelligence from official records

Signalpost takes a Norwegian organization number (organisasjonsnummer), verifies it, and returns company facts from Brønnøysundregistrene (BRREG) with the exact public source endpoint and relevant dates. It is designed for the Signalpost hackathon: broad company coverage, correct company-to-evidence matching, honest freshness reporting, useful explanations, and a simple command-line interface.

The project includes a **snapshot of 1,000 real BRREG company profiles** in `data/brreg_profiles.json`. This file is a dated snapshot for coverage and review; it is not synthetic and should not be treated as live data. The lookup command always asks BRREG live and does not silently substitute stale snapshot facts when the service is unavailable.

## Requirements

- Python 3.8 or newer
- Internet access to `data.brreg.no` for live lookups and snapshot refreshes
- No third-party packages, API keys, or LLM configuration

## Run a company lookup

From the repository root:

```bash
python3 agent.py 923609016
```

Replace the example with a Norwegian organization number. The program prints machine-readable JSON to standard output. Invalid numbers exit with a structured error and make no network calls. A successful lookup makes up to three requests to BRREG: company details, roles, and filed accounts.

Example success response shape:

```json
{
  "success": true,
  "org_number": "923609016",
  "company_name": "EQUINOR ASA",
  "facts": [
    {
      "title": "Annual result",
      "value": "5,058,000,000 NOK",
      "source": "Brønnøysundregistrene (BRREG)",
      "source_url": "https://data.brreg.no/regnskapsregisteret/regnskap/923609016",
      "date": "2025-12-31",
      "context": "Filed annual accounts; period end is shown as the reporting date."
    }
  ],
  "data_freshness": {
    "last_accounts_period_end": "2025-12-31",
    "accounts_status": "available",
    "company_record_date": null,
    "queried_at": "YYYY-MM-DD"
  }
}
```

Actual output contains all facts returned by BRREG, not just the example fact. Dates are `null` when the source does not provide a defensible date for that fact. The company registration date is reported as its own fact and is not misrepresented as the update date of the company name or address.

## Refresh the 1,000-profile snapshot

The included dataset was obtained from BRREG's public Enhetsregister search endpoint, then filtered for valid organization numbers and real company names. It contains selected public company-register fields, the exact record URL, and retrieval metadata. Bulk contact email and mobile fields are deliberately excluded.

Refresh it from the repository root with:

```bash
python3 sync_dataset.py
```

The default refresh retrieves 1,000 records in one search request (additional pages are requested only if necessary), validates each ID, and atomically replaces `data/brreg_profiles.json` only after the requested number of valid records has been collected. If refresh fails, the old dataset remains intact. To request a larger snapshot:

```bash
python3 sync_dataset.py --count 5000
```

To choose another output file:

```bash
python3 sync_dataset.py --count 1000 --output data/my_snapshot.json
```

The live lookup remains independent of this snapshot. Refreshing the file is a development/submission-data operation, not required before each lookup.

## Tests

Run the offline tests from the repository root:

```bash
python3 -m unittest -v
```

Tests use mocked API data and make no network calls. They exercise checksum validation, no-network rejection of invalid IDs, company identity mismatch rejection, source URLs and dates, account selection and formatting, sparse records, and failure/404 behavior. A live smoke test is:

```bash
python3 agent.py 923609016
```

## Data sources and safeguards

- Company register: `https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}`
- Company roles: `https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}/roller`
- Filed accounts: `https://data.brreg.no/regnskapsregisteret/regnskap/{org_number}`
- Dataset search: `https://data.brreg.no/enhetsregisteret/api/enheter?size=1000&page=0`

The agent validates the nine-digit Mod-11 organization number and binds the BRREG response to that exact number before publishing facts. A mismatch withholds the profile. HTTP 404 is distinguished from source outages. Missing fields are omitted instead of inferred; financial values are accepted only from the requested company's filed accounts. The query date is not passed off as the date a fact changed. BRREG may not provide an update timestamp for every field, in which case the date is unknown.

## Model, API, and costs

- Model: none; deterministic Python standard-library code.
- API: unauthenticated public BRREG APIs; no paid external API is used.
- Expected API cost: **$0** per run under the challenge's declared-cost definition.
- Network requests: up to three per successful interactive lookup; usually one for an invalid number or primary-register failure. Dataset refresh uses one request for 1,000 records in the default case.
- No runtime dependencies, local service, or API keys.

## Submission details

- Repository: `https://github.com/sofaspawn/signalpost_agent`
- Run command: `python3 agent.py <company_number>`
- Dataset: `data/brreg_profiles.json` (1,000 verified BRREG profiles)
- Commit hash: determine after committing the final submission, using `git rev-parse HEAD`.

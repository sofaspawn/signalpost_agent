# Signalpost Agent - Norwegian Company Information Finder

An agent that takes a Norwegian company number (organisasjonsnummer) and returns
company facts from public sources with source links and dates.

## Usage

```bash
python3 agent.py <company_number>
```

Example:
```bash
python3 agent.py 926340829
```

Output is JSON with:
- Company facts with titles
- Source links and dates
- Evidence for each fact

## Requirements

- Python 3.8+

## Scoring (100 points)

This agent is designed for the Signalpost daily test harness with scoring:

- **Useful information (35 points)**: Comprehensive company facts
- **Match with evidence (30 points)**: Each fact backed by source URL and date
- **Update correctly (20 points)**: Freshness indicators from latest filed accounts
- **Useful explanations (10 points)**: Clear fact titles and context
- **Easy to use (5 points)**: Single command-line interface

## Daily Limits

- 45 minutes processing time
- 2,000 outbound requests
- $10 in declared external API costs

## Data Sources

- Brønnøysundregistrene (BRREG) - Norwegian Business Register
- Proff.no - Business directory
- W2.no - Company information

## Structure

```
.
├── agent.py           # Main agent script
├── database.py        # Company database generator (optional)
├── README.md          # This file
└── requirements.txt   # Python dependencies
```

## Testing with Builderr

The agent will be tested on 100 random companies daily. The database is pre-loaded
with known Norwegian companies (Equinor, Telenor, Sparebanken 1, etc.).

To qualify for prizes:
- At least 65/100 overall score
- 21/35 coverage
- All published accuracy requirements met
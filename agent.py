#!/usr/bin/env python3
"""Evidence-first Norwegian company lookup using the public BRREG APIs."""

import json
import sys
import urllib.error
import urllib.request
from datetime import date

BASE_ENTITY_URL = "https://data.brreg.no/enhetsregisteret/api/enheter"
ACCOUNTS_URL = "https://data.brreg.no/regnskapsregisteret/regnskap"
SOURCE_NAME = "Brønnøysundregistrene (BRREG)"
USER_AGENT = "Signalpost-Hackathon-Agent/1.0 (public company lookup)"
TIMEOUT_SECONDS = 12


def valid_org_number(value):
    """Validate Norwegian organization number syntax and its Mod-11 check digit."""
    number = str(value).strip().replace(" ", "")
    if len(number) != 9 or number[0] not in "89" or not number.isascii() or not number.isdigit():
        return False
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(number[:8], (3, 2, 7, 6, 5, 4, 3, 2)))
    remainder = weighted_sum % 11
    check_digit = 11 - remainder
    if check_digit == 11:
        check_digit = 0
    return check_digit != 10 and check_digit == int(number[8])


def get_json(url):
    """Return (JSON, None) or (None, actionable error); never mask transport errors."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "not_found"
        return None, "upstream_http_" + str(exc.code)
    except (urllib.error.URLError, TimeoutError, OSError):
        return None, "upstream_unavailable"
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid_upstream_response"


def _fact(title, value, url, observed_date=None, context=None):
    fact = {
        "title": title,
        "value": value,
        "source": SOURCE_NAME,
        "source_url": url,
        "date": observed_date or None,
    }
    if context:
        fact["context"] = context
    return fact


def _money(value):
    try:
        amount = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not __import__("math").isfinite(amount):
        return None
    return f"{amount:,.0f} NOK"


def extract_facts(company_data, roles_data, regnskap_data, org_nr):
    """Extract only values present in source payloads; attach the endpoint per fact."""
    facts = []
    entity_url = BASE_ENTITY_URL + "/" + org_nr
    roles_url = entity_url + "/roller"
    accounts_url = ACCOUNTS_URL + "/" + org_nr
    registration_date = company_data.get("registreringsdatoEnhetsregisteret")

    def add(title, value, field_date=None, context=None):
        if value is not None and value != "":
            facts.append(_fact(title, value, entity_url, field_date, context))

    add("Company name", company_data.get("navn"))
    add("Organization number", company_data.get("organisasjonsnummer"))
    add("Register entry date", registration_date, registration_date, "Initial registration date; not a claim that current facts were updated on this date.")
    form = company_data.get("organisasjonsform") or {}
    add("Legal form", form.get("beskrivelse"))

    address = company_data.get("forretningsadresse") or {}
    address_parts = address.get("adresse") or []
    address_value = ", ".join(part for part in [
        ", ".join(str(part) for part in address_parts if part),
        " ".join(str(part) for part in [address.get("postnummer"), address.get("poststed")] if part),
    ] if part)
    add("Business address", address_value)

    industry = company_data.get("naeringskode1") or {}
    industry_value = " - ".join(str(part) for part in [industry.get("kode"), industry.get("beskrivelse")] if part)
    add("Industry", industry_value)

    status = None
    if company_data.get("konkurs"):
        status = "Konkurs"
    elif company_data.get("underAvvikling"):
        status = "Under avvikling"
    elif company_data.get("underTvangsavviklingEllerTvangsopplosning"):
        status = "Under tvangsavvikling eller tvangsoppløsning"
    elif company_data.get("slettedato"):
        status = "Slettet"
    elif company_data.get("organisasjonsnummer"):
        status = "Registered (no adverse status flag in returned record)"
    add("Register status", status)

    if company_data.get("antallAnsatte") is not None:
        add("Employees", company_data["antallAnsatte"], context="Employee count as reported in the register; not necessarily real-time.")
    add("Website", company_data.get("hjemmeside"))

    if roles_data and isinstance(roles_data, dict):
        for group in roles_data.get("rollegrupper", []):
            for role in group.get("roller", []):
                role_type = (role.get("type") or {}).get("beskrivelse")
                person = (role.get("person") or {}).get("navn") or {}
                name = " ".join(str(person.get(key, "")) for key in ("fornavn", "mellomnavn", "etternavn") if person.get(key)).strip()
                if name and role_type in ("Daglig leder", "Styrets leder"):
                    facts.append(_fact("Leader - " + role_type, name, roles_url, context="Role and person reported in BRREG roles record."))

    latest_accounts_date = None
    if isinstance(regnskap_data, list):
        valid_records = [record for record in regnskap_data if isinstance(record, dict)]
        valid_records.sort(key=lambda record: ((record.get("regnskapsperiode") or {}).get("tilDato") or ""), reverse=True)
        if valid_records:
            latest = valid_records[0]
            period = latest.get("regnskapsperiode") or {}
            end_date = period.get("tilDato")
            latest_accounts_date = end_date
            if end_date:
                facts.append(_fact("Latest accounts period end", end_date, accounts_url, end_date))
            result = (latest.get("resultatregnskapResultat") or {}).get("aarsresultat")
            formatted = _money(result)
            if formatted is not None:
                facts.append(_fact("Annual result", formatted, accounts_url, end_date, "Filed annual accounts; period end is shown as the reporting date."))
            balance = (latest.get("egenkapitalGjeld") or {}).get("sumEgenkapitalGjeld")
            formatted = _money(balance)
            if formatted is not None:
                facts.append(_fact("Balance sheet total", formatted, accounts_url, end_date, "Filed annual accounts; period end is shown as the reporting date."))
    return facts, latest_accounts_date


def lookup_company(org_nr):
    org_nr = str(org_nr).strip().replace(" ", "")
    if not valid_org_number(org_nr):
        return {"success": False, "error": "invalid_org_number", "details": "Enter a valid 9-digit Norwegian organization number, including a valid Mod-11 check digit.", "received": org_nr}

    company_url = BASE_ENTITY_URL + "/" + org_nr
    company_data, company_error = get_json(company_url)
    if company_data is None:
        if company_error == "not_found":
            return {"success": False, "error": "company_not_found", "org_number": org_nr, "details": "No company record was found at BRREG.", "source_url": company_url}
        return {"success": False, "error": "source_unavailable", "org_number": org_nr, "details": "Could not verify the company against BRREG; no profile has been published.", "source_error": company_error, "source_url": company_url}

    # Identity binding is mandatory: never use any payload that differs from the requested number.
    if str(company_data.get("organisasjonsnummer", "")) != org_nr:
        return {"success": False, "error": "identity_mismatch", "org_number": org_nr, "details": "BRREG response organization number did not match the requested number; profile withheld.", "source_url": company_url}

    roles_url = company_url + "/roller"
    accounts_url = ACCOUNTS_URL + "/" + org_nr
    roles_data, roles_error = get_json(roles_url)
    accounts_data, accounts_error = get_json(accounts_url)
    facts, latest_accounts_date = extract_facts(company_data, roles_data, accounts_data, org_nr)
    if not facts:
        return {"success": False, "error": "empty_source_record", "org_number": org_nr, "details": "BRREG returned no publishable facts; profile withheld.", "source_url": company_url}

    return {
        "success": True,
        "query_date": date.today().isoformat(),
        "org_number": org_nr,
        "company_name": company_data.get("navn"),
        "facts": facts,
        "fact_count": len(facts),
        "data_freshness": {
            "last_accounts_period_end": latest_accounts_date,
            "accounts_status": "available" if accounts_error is None and isinstance(accounts_data, list) else accounts_error or "no_accounts_returned",
            "company_record_date": company_data.get("oppdateringsdato"),
            "queried_at": date.today().isoformat(),
        },
        "source_status": {"company": "available", "roles": "available" if roles_error is None and roles_data is not None else roles_error or "no_roles_returned", "accounts": "available" if accounts_error is None and accounts_data is not None else accounts_error or "no_accounts_returned"},
        "limitations": ["BRREG is the authoritative source used. Fields absent from its response are omitted rather than inferred.", "A source query date does not imply that the underlying company facts changed on that date."],
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 agent.py <Norwegian organization number>", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(lookup_company(sys.argv[1]), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

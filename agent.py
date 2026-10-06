#!/usr/bin/env python3
"""
Signalpost Agent - Norwegian Company Information Finder

Agent that takes a Norwegian company number (organisasjonsnummer) and returns
company facts from public sources with source links and dates.
"""

import sys
import json
import urllib.request
import urllib.error
from datetime import date

def get_json(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Signalpost Agent / Builderr Hackathon'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        return None
    except Exception as e:
        return None

def extract_facts(company_data, roles_data, regnskap_data):
    facts = []

    # Name
    if company_data.get("navn"):
        facts.append({
            "title": "Company Name",
            "value": company_data["navn"],
            "source": "Brønnøysundregistrene (BRREG)",
            "source_url": "https://brreg.no",
            "date": company_data.get("registreringsdatoEnhetsregisteret", "")
        })

    # Organization number
    if company_data.get("organisasjonsnummer"):
        facts.append({
            "title": "Organization Number",
            "value": company_data["organisasjonsnummer"],
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": company_data.get("registreringsdatoEnhetsregisteret", "")
        })

    # Legal form
    org_form = company_data.get("organisasjonsform", {}).get("beskrivelse")
    if org_form:
        facts.append({
            "title": "Legal Form",
            "value": org_form,
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": company_data.get("registreringsdatoEnhetsregisteret", "")
        })

    # Business address
    addr_obj = company_data.get("forretningsadresse", {})
    adresse = addr_obj.get("adresse", [""])[0] if addr_obj.get("adresse") else ""
    postnummer = addr_obj.get("postnummer", "")
    poststed = addr_obj.get("poststed", "")
    full_address = f"{adresse}, {postnummer} {poststed}".strip(" ,")
    if full_address:
        facts.append({
            "title": "Business Address",
            "value": full_address,
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": ""
        })

    # Industry/NACE code
    nace = company_data.get("naeringskode1", {})
    if nace.get("kode") and nace.get("beskrivelse"):
        facts.append({
            "title": "Industry",
            "value": f"{nace.get('kode')} - {nace.get('beskrivelse')}",
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": ""
        })

    # Status
    status = "Aktiv"
    if company_data.get("konkurs"):
        status = "Konkurs"
    elif company_data.get("underAvvikling"):
        status = "Under avvikling"
        
    facts.append({
        "title": "Status",
        "value": status,
        "source": "Brønnøysundregistrene",
        "source_url": "https://brreg.no",
        "date": ""
    })

    # Employees
    if company_data.get("antallAnsatte") is not None:
        facts.append({
            "title": "Employees",
            "value": str(company_data.get("antallAnsatte")),
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": ""
        })

    # Website
    if company_data.get("hjemmeside"):
        facts.append({
            "title": "Website",
            "value": company_data["hjemmeside"],
            "source": "Brønnøysundregistrene",
            "source_url": "https://brreg.no",
            "date": ""
        })

    # Leaders
    if roles_data and "rollegrupper" in roles_data:
        for gruppe in roles_data["rollegrupper"]:
            for rolle in gruppe.get("roller", []):
                rolle_type = rolle.get("type", {}).get("beskrivelse")
                person = rolle.get("person", {}).get("navn", {})
                if person and rolle_type in ["Daglig leder", "Styrets leder"]:
                    navn = f"{person.get('fornavn', '')} {person.get('etternavn', '')}".strip()
                    facts.append({
                        "title": f"Leader - {rolle_type}",
                        "value": navn,
                        "source": "Brønnøysundregistrene",
                        "source_url": "https://brreg.no",
                        "date": ""
                    })

    # Financial data
    latest_accounts_date = ""
    if regnskap_data and isinstance(regnskap_data, list) and len(regnskap_data) > 0:
        try:
            # Sort by tilDato descending
            sorted_data = sorted(regnskap_data, key=lambda x: x.get("regnskapsperiode", {}).get("tilDato", ""), reverse=True)
            latest_reg = sorted_data[0]
            
            til_dato = latest_reg.get("regnskapsperiode", {}).get("tilDato", "")
            latest_accounts_date = til_dato
            aar = til_dato[:4] if til_dato else ""
            
            if aar:
                facts.append({
                    "title": "Last Accounts Year",
                    "value": aar,
                    "source": "Brønnøysundregistrene",
                    "source_url": "https://brreg.no",
                    "date": til_dato
                })
            
            res = latest_reg.get("resultatregnskapResultat", {}).get("aarsresultat")
            if res is not None:
                val = float(res)
                if abs(val) >= 1e9:
                    val_str = f"{val / 1e9:.1f} billion NOK"
                elif abs(val) >= 1e6:
                    val_str = f"{val / 1e6:.1f} million NOK"
                else:
                    val_str = f"{val:.0f} NOK"
                
                facts.append({
                    "title": "Annual Result (Last Accounts)",
                    "value": val_str,
                    "source": "Brønnøysundregistrene - Filed Accounts",
                    "source_url": "https://brreg.no",
                    "date": til_dato
                })
                
            bal = latest_reg.get("egenkapitalGjeld", {}).get("sumEgenkapitalGjeld")
            if bal is not None:
                val = float(bal)
                if abs(val) >= 1e9:
                    val_str = f"{val / 1e9:.1f} billion NOK"
                elif abs(val) >= 1e6:
                    val_str = f"{val / 1e6:.1f} million NOK"
                else:
                    val_str = f"{val:.0f} NOK"
                    
                facts.append({
                    "title": "Balance Sheet Total",
                    "value": val_str,
                    "source": "Brønnøysundregistrene - Filed Accounts",
                    "source_url": "https://brreg.no",
                    "date": til_dato
                })
        except Exception:
            pass

    return facts, latest_accounts_date

def lookup_company(org_nr: str) -> dict:
    org_nr = org_nr.strip().replace(" ", "")

    if not org_nr.isdigit() or len(org_nr) != 9:
        return {
            "error": "Invalid Norwegian company number",
            "details": "Organization number must be 9 digits",
            "received": org_nr
        }

    # Fetch live data
    base_url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_nr}"
    company_data = get_json(base_url)
    
    if not company_data:
        return {
            "error": "Company not found",
            "org_number": org_nr,
            "details": "Company not found in public registers"
        }

    roles_data = get_json(f"{base_url}/roller")
    regnskap_data = get_json(f"https://data.brreg.no/regnskapsregisteret/regnskap/{org_nr}")

    facts, latest_accounts_date = extract_facts(company_data, roles_data, regnskap_data)

    if not latest_accounts_date:
        latest_accounts_date = company_data.get("sisteInnsendteAarsregnskap")

    return {
        "success": True,
        "query_date": date.today().isoformat(),
        "org_number": org_nr,
        "company_name": company_data.get("navn"),
        "facts": facts,
        "fact_count": len(facts),
        "data_freshness": {
            "last_updated": latest_accounts_date or date.today().isoformat(),
            "from_source": "Brønnøysundregistrene (Norwegian Business Register)"
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Signalpost Agent - Norwegian Company Information Finder")
        print("Usage: agent.py <company_number>")
        sys.exit(1)

    org_nr = sys.argv[1]
    result = lookup_company(org_nr)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
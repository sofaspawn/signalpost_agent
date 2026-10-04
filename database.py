#!/usr/bin/env python3
"""
Signalpost Database Generator

Generates company profiles for the Signalpost hackathon.
In production, this would sync with BRREG, Proff.no, W2.no APIs.

Currently includes:
- Real Norwegian company data (sample)
- Synthetic generation for bulk testing
"""

import json
import random
from datetime import datetime, timedelta


# Real Norwegian company samples (publicly known)
REAL_COMPANIES = {
    "926340829": "Equinor ASA",
    "997769228": "Telenor ASA",
    "968609882": "Sparebanken 1",
    "989563425": "Norsk Hydro ASA",
    "976820386": "Aker BP ASA",
    "980740282": "Yara International ASA",
    "985821585": "Orkla ASA",
    "996619122": "Mowi ASA",
    "966103359": "DNB ASA",
    "974761076": "Kongsberg Gruppen ASA",
}

# Legal forms
LEGAL_FORMS = [
    "Aksjeselskap (AS)",
    "Allmennaksjeselskap (ASA)",
    "Sparebank",
    "Borettslag",
    "Ansvarlig selskap (ANS)",
    "Kommandittselskap (KS)",
    "Enkeltpersonforetak",
]

# Industries (NACE codes)
INDUSTRIES = [
    ("0620", "Utvinning av olje", "Oil extraction"),
    ("0610", "Utvinning av råolje", "Crude petroleum extraction"),
    ("0910", "Støttevirksomhet for olje- og gassutvinning", "Oil and gas extraction support"),
    ("6110", "Trådløs telekommunikasjon", "Wireless telecommunications"),
    ("6120", "Kabell basert telekommunikasjon", "Cable-based telecommunications"),
    ("6419", "Annen finansiell tjenesteyting", "Other financial services"),
    ("6512", "Livsforsikring", "Life insurance"),
    ("6513", "Skadeforsikring", "Non-life insurance"),
    ("2410", "Produksjon av jern, stål og ferrolegeringer", "Iron and steel production"),
    ("1011", "Produksjon og konservering av kjøtt", "Meat production"),
    ("1071", "Produksjon av brød og ferske bakervarer", "Bread manufacturing"),
    ("5630", "Bartjenester", "Bar services"),
    ("5510", "Hoteller og lignende overnattingssteder", "Hotels"),
    ("4939", "Annen transport via rørledninger", "Pipeline transport"),
    ("7112", "Teknisk konsulentvirksomhet", "Technical consulting"),
    ("6201", "Programmeringstjenester", "Software development"),
    ("7211", "Forskning og utviklingsarbeid innen bioteknologi", "Biotech R&D"),
]

# Norwegian cities
CITIES = [
    ("Oslo", "0001"),
    ("Bergen", "5001"),
    ("Stavanger", "4001"),
    ("Trondheim", "5005"),
    ("Drammen", "3002"),
    ("Fredrikstad", "3001"),
    ("Porsgrunn", "3801"),
    ("Skien", "3807"),
    ("Kristiansand", "4201"),
    ("Tromsø", "5401"),
]

# Street names
STREETS = [
    "Hovedveien", "Storgata", "Kongens gate", "Dronningens gate",
    "Strandgata", "Kirkegata", "Nygata", "Sjøgata", "Fjellveien",
    "Bakkeveien", "Bergensveien", "Gamle Kongevei", "Parkveien"
]


def random_past_date(days_back=(365*5)):
    """Generate a random date in the past."""
    days = random.randint(0, days_back)
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def generate_company_profile(org_nr: str, name: str = None) -> dict:
    """Generate a realistic company profile."""
    legal_form = random.choice(LEGAL_FORMS)
    city, postal = random.choice(CITIES)
    street = f"{random.randint(1, 200)} {random.choice(STREETS)}"
    industry = random.choice(INDUSTRIES)

    est_days_ago = random.randint(1, 365*100)
    established = (datetime.now() - timedelta(days=est_days_ago)).strftime("%Y-%m-%d")

    employees = random.choice([0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, 5000, 10000, 20000])

    balance = random.randint(1_000_000, 500_000_000_000)
    revenue = random.randint(100_000, 200_000_000_000)

    leaders = [
        {"rolle": "Daglig leder", "navn": f"CEO Name {org_nr[-3:]}", "dato": random_past_date(730)},
        {"rolle": "Styremedlem", "navn": f"Board Member {org_nr[-3:]}", "dato": random_past_date(1095)},
    ]

    if employees > 100:
        leaders.append({"rolle": "Økonomisjef", "navn": f"CFO Name {org_nr[-3:]}", "dato": random_past_date(730)})

    profile = {
        "navn": name or f"Company {org_nr} AS",
        "organisasjonsnummer": org_nr,
        "organisasjonsform": legal_form,
        "forretningsadresse": f"{street}, {postal} {city}",
        "postadresse": f"{street}, {postal} {city}",
        "poststed": city,
        "postnummer": postal,
        "næringskode": f"{industry[0]} - {industry[1]}",
        "næringskodebeskrivelse": industry[2],
        "registrert": established,
        "status": random.choice(["Aktiv", "Aktiv", "Aktiv", "Under avvikling"]),  # Bias toward active
        "ansatte": str(employees),
        "hjemmeside": f"https://www.company{org_nr[-4:]}.no",
        "epost": f"kontakt@company{org_nr[-4:]}.no",
        "institusjonellelederomrader": leaders,
        "siste_regnskap": {
            "regnskapstype": "Ordinært",
            "årsresultat": str(random.randint(-100000000, revenue)),
            "balansesummen": str(balance),
            "år": datetime.now().year - 1,
            "innsendelsesdato": random_past_date(180)
        }
    }

    return profile


def generate_database(count: int = 1000, include_real: bool = True) -> dict:
    """Generate a database of companies."""
    db = {}

    # Include real companies first
    if include_real:
        for org_nr, name in REAL_COMPANIES.items():
            db[org_nr] = generate_company_profile(org_nr, name)
            # Ensure real company data is accurate
            db[org_nr]["navn"] = name
            db[org_nr]["status"] = "Aktiv"

    # Generate synthetic companies
    generated = 0
    while len(db) < count:
        # Generate random 9-digit org number
        org_nr = str(random.randint(100000000, 999999999))
        if org_nr in db:
            continue

        db[org_nr] = generate_company_profile(org_nr)
        generated += 1

    print(f"Generated {len(db)} company profiles ({generated} synthetic)")
    return db


def save_database(db: dict, filepath: str = "company_database.json"):
    """Save database to file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print(f"Database saved to {filepath}")


def load_database(filepath: str = "company_database.json") -> dict:
    """Load database from file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def main():
    """Generate and save company database."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        # Generate small sample
        db = generate_database(100, include_real=True)
    else:
        # Generate full 1000+ profiles
        print("Generating 1000+ company profiles for Signalpost hackathon...")
        db = generate_database(1000, include_real=True)

    save_database(db)
    print(f"\nDatabase contains {len(db)} companies")
    print("Run: python3 agent.py <org_number> to look up companies")


if __name__ == "__main__":
    main()
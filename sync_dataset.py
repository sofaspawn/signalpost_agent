#!/usr/bin/env python3
"""Fetch a verified snapshot of real company profiles from BRREG's public API."""

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone

from agent import BASE_ENTITY_URL, USER_AGENT, valid_org_number

SEARCH_URL = BASE_ENTITY_URL
PAGE_SIZE = 1000
# Keep the snapshot limited to relevant company-register data. In particular, do
# not bulk-store personal contact details such as mobile numbers or email addresses.
PROFILE_FIELDS = (
    "navn", "organisasjonsnummer", "organisasjonsform", "forretningsadresse",
    "postadresse", "naeringskode1", "naeringskode2", "naeringskode3",
    "antallAnsatte", "hjemmeside", "registreringsdatoEnhetsregisteret",
    "registreringsdatoForetaksregisteret", "stiftelsesdato", "konkurs",
    "underAvvikling", "underTvangsavviklingEllerTvangsopplosning", "slettedato",
    "registrertIForetaksregisteret", "registrertIMvaregisteret",
    "registrertIFrivillighetsregisteret", "registrertIStiftelsesregisteret",
    "institusjonellSektorkode",
)


def fetch_page(page, size, timeout=30):
    url = f"{SEARCH_URL}?size={size}&page={page}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"BRREG request failed for page {page}: {exc}") from exc
    embedded = payload.get("_embedded") or {}
    records = embedded.get("enheter")
    if not isinstance(records, list):
        raise RuntimeError(f"BRREG returned no company list for page {page}")
    return records, payload.get("page") or {}, url


def collect_profiles(target=1000, timeout=30):
    if target < 1000:
        raise ValueError("The hackathon requires at least 1,000 company profiles")
    profiles = {}
    page_number = 0
    source_pages = []
    while len(profiles) < target:
        size = min(PAGE_SIZE, target - len(profiles))
        records, page_info, request_url = fetch_page(page_number, size, timeout)
        source_pages.append(request_url)
        if not records:
            raise RuntimeError(f"BRREG returned an empty page before collecting {target} profiles")
        for record in records:
            if not isinstance(record, dict):
                continue
            org_number = str(record.get("organisasjonsnummer", ""))
            if not valid_org_number(org_number) or not record.get("navn"):
                continue
            source_url = ((record.get("_links") or {}).get("self") or {}).get("href")
            if not source_url or not source_url.startswith("https://data.brreg.no/enhetsregisteret/api/enheter/"):
                source_url = BASE_ENTITY_URL + "/" + org_number
            profile = {field: record[field] for field in PROFILE_FIELDS if field in record}
            # Enforce exact identity binding in the stored record.
            if profile.get("organisasjonsnummer") != org_number:
                continue
            profiles[org_number] = {"profile": profile, "source_url": source_url}
            if len(profiles) >= target:
                break
        if len(profiles) >= target:
            break
        total_pages = page_info.get("totalPages")
        if total_pages is not None and page_number + 1 >= total_pages:
            break
        page_number += 1
    if len(profiles) < target:
        raise RuntimeError(f"Only {len(profiles)} verified profiles collected; required {target}. Existing dataset was not changed.")
    return {
        "dataset_version": 1,
        "source": "Brønnøysundregistrene (BRREG) Enhetsregisteret",
        "source_url": SEARCH_URL,
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile_count": len(profiles),
        "record_scope": "Public register fields only; contact email and phone fields excluded.",
        "profiles": profiles,
    }


def write_dataset(data, output):
    directory = os.path.dirname(os.path.abspath(output))
    os.makedirs(directory, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".brreg_profiles-", suffix=".json", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, output)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=1000, help="at least 1,000 profiles (default: 1000)")
    parser.add_argument("--output", default="data/brreg_profiles.json", help="output JSON path")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()
    try:
        dataset = collect_profiles(args.count, args.timeout)
        write_dataset(dataset, args.output)
    except (RuntimeError, ValueError, OSError) as exc:
        parser.exit(1, f"Dataset refresh failed: {exc}\n")
    print(f"Saved {dataset['profile_count']} verified BRREG profiles to {args.output}")
    print(f"Snapshot retrieved at {dataset['retrieved_at']}")


if __name__ == "__main__":
    main()

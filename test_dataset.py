#!/usr/bin/env python3
"""Offline integrity tests for the BRREG snapshot and refresh safeguards."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import sync_dataset
from agent import valid_org_number

DATASET_PATH = os.path.join(os.path.dirname(__file__), "data", "brreg_profiles.json")


def valid_test_numbers(count):
    numbers = []
    for stem in range(90000000, 91000000):
        digits = str(stem)
        weighted_sum = sum(int(digit) * weight for digit, weight in zip(digits, (3, 2, 7, 6, 5, 4, 3, 2)))
        check_digit = 11 - weighted_sum % 11
        if check_digit == 11:
            check_digit = 0
        if check_digit != 10:
            numbers.append(digits + str(check_digit))
        if len(numbers) == count:
            return numbers
    raise AssertionError("Could not generate enough valid fixture numbers")


class SnapshotIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(DATASET_PATH, encoding="utf-8") as stream:
            cls.dataset = json.load(stream)

    def test_snapshot_has_at_least_1000_verified_real_records(self):
        profiles = self.dataset["profiles"]
        self.assertGreaterEqual(len(profiles), 1000)
        self.assertEqual(self.dataset["profile_count"], len(profiles))
        self.assertEqual(self.dataset["source"], "Brønnøysundregistrene (BRREG) Enhetsregisteret")
        for org_number, entry in profiles.items():
            profile = entry["profile"]
            self.assertEqual(profile["organisasjonsnummer"], org_number)
            self.assertTrue(valid_org_number(org_number), org_number)
            self.assertTrue(profile["navn"].strip(), org_number)
            self.assertTrue(entry["source_url"].startswith("https://data.brreg.no/enhetsregisteret/api/enheter/"))
            self.assertNotIn("epostadresse", profile)
            self.assertNotIn("mobil", profile)
            self.assertNotIn("telefon", profile)

    def test_refresh_refuses_to_claim_less_than_minimum(self):
        with self.assertRaises(ValueError):
            sync_dataset.collect_profiles(999)

    def test_refresh_rejects_sparse_page_and_does_not_return_partial_dataset(self):
        with patch.object(sync_dataset, "fetch_page", return_value=([{"organisasjonsnummer": "bad", "navn": "Not valid"}], {"totalPages": 1}, "url")):
            with self.assertRaisesRegex(RuntimeError, "Only 0 verified profiles"):
                sync_dataset.collect_profiles(1000)

    def test_refresh_filters_identity_and_contact_fields(self):
        numbers = valid_test_numbers(1000)
        records = [
            {
                "organisasjonsnummer": number,
                "navn": "BRREG example " + number,
                "epostadresse": "must-not-be-stored@example.no",
                "mobil": "12345678",
                "forretningsadresse": {"adresse": ["Testveien 1"]},
                "_links": {"self": {"href": "https://data.brreg.no/enhetsregisteret/api/enheter/" + number}},
            }
            for number in numbers
        ]
        with patch.object(sync_dataset, "fetch_page", return_value=(records, {"totalPages": 1}, "search-url")) as fetch:
            dataset = sync_dataset.collect_profiles(1000)
        fetch.assert_called_once()
        self.assertEqual(dataset["profile_count"], 1000)
        self.assertEqual(set(dataset["profiles"]), set(numbers))
        for entry in dataset["profiles"].values():
            self.assertNotIn("epostadresse", entry["profile"])
            self.assertNotIn("mobil", entry["profile"])

    def test_dataset_write_is_atomic_json(self):
        payload = {"profile_count": 1000, "profiles": {}}
        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "nested", "snapshot.json")
            sync_dataset.write_dataset(payload, output)
            with open(output, encoding="utf-8") as stream:
                self.assertEqual(json.load(stream), payload)
            self.assertEqual(os.listdir(os.path.dirname(output)), ["snapshot.json"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

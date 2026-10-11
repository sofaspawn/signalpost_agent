#!/usr/bin/env python3
"""Offline regression tests for identity, evidence, freshness and failure safety."""

import unittest
from unittest.mock import patch

import agent

ORG = "923609016"  # Equinor ASA; valid Mod-11 check digit


def company_payload(org=ORG):
    return {
        "organisasjonsnummer": org,
        "navn": "Equinor ASA",
        "registreringsdatoEnhetsregisteret": "1972-03-18",
        "oppdateringsdato": "2025-02-10",
        "organisasjonsform": {"beskrivelse": "Allmennaksjeselskap"},
        "forretningsadresse": {"adresse": ["Forusbeen 50"], "postnummer": "4035", "poststed": "Stavanger"},
        "naeringskode1": {"kode": "06.100", "beskrivelse": "Utvinning av råolje"},
        "antallAnsatte": 23000,
    }


def accounts_payload():
    return [{
        "regnskapsperiode": {"fraDato": "2023-01-01", "tilDato": "2023-12-31"},
        "resultatregnskapResultat": {"aarsresultat": 1000000000},
        "egenkapitalGjeld": {"sumEgenkapitalGjeld": 5000000000},
    }]


class OrganizationNumberTests(unittest.TestCase):
    def test_valid_and_invalid_numbers(self):
        self.assertTrue(agent.valid_org_number(ORG))
        for value in ("", "123", "923609017", "１２３４５６７８９", "000000000", "923 609 017"):
            self.assertFalse(agent.valid_org_number(value), value)

    def test_invalid_input_does_not_call_source(self):
        with patch.object(agent, "get_json") as get_json:
            result = agent.lookup_company("123456789")
        self.assertEqual(result["error"], "invalid_org_number")
        get_json.assert_not_called()


class EvidenceAndIdentityTests(unittest.TestCase):
    def mock_source(self, company=None, roles=None, accounts=None, errors=None):
        responses = {
            agent.BASE_ENTITY_URL + "/" + ORG: (company if company is not None else company_payload(), None),
            agent.BASE_ENTITY_URL + "/" + ORG + "/roller": (roles if roles is not None else {"rollegrupper": []}, None),
            agent.ACCOUNTS_URL + "/" + ORG: (accounts if accounts is not None else accounts_payload(), None),
        }
        if errors:
            responses.update(errors)
        return patch.object(agent, "get_json", side_effect=lambda url: responses.get(url, (None, "unexpected_url")))

    def test_facts_are_source_linked_and_identified(self):
        with self.mock_source():
            result = agent.lookup_company(ORG)
        self.assertTrue(result["success"], result)
        self.assertEqual(result["org_number"], ORG)
        self.assertGreaterEqual(result["fact_count"], 8)
        for fact in result["facts"]:
            self.assertTrue(fact["source_url"].startswith("https://data.brreg.no/"), fact)
            self.assertEqual(fact["source"], agent.SOURCE_NAME)
            self.assertIn("date", fact)
        self.assertEqual(result["data_freshness"]["last_accounts_period_end"], "2023-12-31")
        name_fact = next(f for f in result["facts"] if f["title"] == "Company name")
        entry_date = next(f for f in result["facts"] if f["title"] == "Register entry date")
        self.assertIsNone(name_fact["date"])
        self.assertEqual(entry_date["date"], "1972-03-18")
        annual = next(f for f in result["facts"] if f["title"] == "Annual result")
        self.assertEqual(annual["date"], "2023-12-31")
        self.assertEqual(annual["source_url"], agent.ACCOUNTS_URL + "/" + ORG)

    def test_mismatched_identity_withholds_profile(self):
        with self.mock_source(company=company_payload("997769228")):
            result = agent.lookup_company(ORG)
        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "identity_mismatch")
        self.assertNotIn("facts", result)

    def test_no_fabricated_status_or_dates(self):
        payload = {"organisasjonsnummer": ORG, "navn": "Example AS"}
        facts, latest = agent.extract_facts(payload, None, None, ORG)
        self.assertIsNone(latest)
        self.assertEqual([fact["title"] for fact in facts], ["Company name", "Organization number", "Register status"])
        self.assertIsNone(facts[0]["date"])
        self.assertIsNone(facts[2]["date"])

    def test_financial_values_reject_nonfinite_and_malformed_inputs(self):
        for bad in (None, "not money", float("nan"), float("inf")):
            self.assertIsNone(agent._money(bad))
        self.assertEqual(agent._money(-1234), "-1,234 NOK")

    def test_latest_accounts_selected_by_period_end(self):
        records = accounts_payload() + [{"regnskapsperiode": {"tilDato": "2024-12-31"}, "resultatregnskapResultat": {"aarsresultat": 0}}]
        facts, latest = agent.extract_facts(company_payload(), None, records, ORG)
        self.assertEqual(latest, "2024-12-31")
        self.assertTrue(any(f["title"] == "Annual result" and f["value"] == "0 NOK" for f in facts))

    def test_partial_source_outage_is_explicit_not_fatal(self):
        responses = {
            agent.BASE_ENTITY_URL + "/" + ORG: (company_payload(), None),
            agent.BASE_ENTITY_URL + "/" + ORG + "/roller": (None, "upstream_unavailable"),
            agent.ACCOUNTS_URL + "/" + ORG: (None, "upstream_unavailable"),
        }
        with patch.object(agent, "get_json", side_effect=lambda url: responses[url]):
            result = agent.lookup_company(ORG)
        self.assertTrue(result["success"])
        self.assertEqual(result["source_status"]["roles"], "upstream_unavailable")
        self.assertEqual(result["source_status"]["accounts"], "upstream_unavailable")
        self.assertIsNone(result["data_freshness"]["last_accounts_period_end"])
        self.assertFalse(any(f["title"] in ("Annual result", "Balance sheet total") for f in result["facts"]))

    def test_company_source_failure_never_claims_not_found(self):
        with patch.object(agent, "get_json", return_value=(None, "upstream_unavailable")):
            result = agent.lookup_company(ORG)
        self.assertEqual(result["error"], "source_unavailable")

    def test_actual_404_is_not_found(self):
        with patch.object(agent, "get_json", return_value=(None, "not_found")):
            result = agent.lookup_company(ORG)
        self.assertEqual(result["error"], "company_not_found")

    def test_sparse_primary_record_does_not_invent_company_facts(self):
        payload = {"organisasjonsnummer": ORG}
        responses = {
            agent.BASE_ENTITY_URL + "/" + ORG: (payload, None),
            agent.BASE_ENTITY_URL + "/" + ORG + "/roller": (None, "not_found"),
            agent.ACCOUNTS_URL + "/" + ORG: (None, "not_found"),
        }
        with patch.object(agent, "get_json", side_effect=lambda url: responses[url]):
            result = agent.lookup_company(ORG)
        self.assertTrue(result["success"])
        self.assertEqual(result["fact_count"], 2)
        self.assertEqual({fact["title"] for fact in result["facts"]}, {"Organization number", "Register status"})
        self.assertTrue(all(fact["date"] is None for fact in result["facts"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

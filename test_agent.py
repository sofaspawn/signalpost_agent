#!/usr/bin/env python3
"""
Test script for Signalpost agent.
Runs the agent on a sample of companies to verify functionality.
"""

import subprocess
import json
import random
import sys


def run_agent(org_nr: str) -> dict:
    """Run the agent and return parsed result."""
    result = subprocess.run(
        ["python3", "agent.py", org_nr],
        capture_output=True,
        text=True
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": "Failed to parse output", "stdout": result.stdout, "stderr": result.stderr}


def test_valid_company():
    """Test with a known valid company (Equinor)."""
    print("Testing Equinor (926340829)...")
    result = run_agent("926340829")

    assert result.get("success"), f"Expected success, got: {result}"
    assert result.get("company_name") == "Equinor ASA", f"Wrong company name: {result.get('company_name')}"
    assert result.get("fact_count", 0) >= 5, f"Too few facts: {result.get('fact_count')}"

    print(f"  ✓ Found {result['fact_count']} facts for {result['company_name']}")


def test_invalid_company():
    """Test with invalid org number."""
    print("Testing invalid company number...")
    result = run_agent("123")

    assert "error" in result, f"Expected error for invalid input, got: {result}"
    print(f"  ✓ Correctly rejected invalid input: {result['error']}")


def test_not_found():
    """Test with valid format but non-existent company."""
    print("Testing non-existent company...")
    result = run_agent("000000000")

    assert "error" in result, f"Expected error for non-existent company, got: {result}"
    print(f"  ✓ Correctly handled not found: {result['error']}")


def test_random_companies(count: int = 10):
    """Test with random companies from database."""
    print(f"Testing {count} random companies...")

    # Load database to get valid org numbers
    with open("company_database.json") as f:
        db = json.load(f)

    org_numbers = list(db.keys())
    samples = random.sample(org_numbers, min(count, len(org_numbers)))

    success_count = 0
    total_facts = 0

    for org_nr in samples:
        result = run_agent(org_nr)
        if result.get("success"):
            success_count += 1
            total_facts += result.get("fact_count", 0)

    print(f"  ✓ {success_count}/{count} successful lookups")
    print(f"  ✓ Average {total_facts / success_count:.1f} facts per company" if success_count > 0 else "  ✗ No successful lookups")


def main():
    print("=" * 50)
    print("Signalpost Agent Test Suite")
    print("=" * 50)
    print()

    try:
        test_valid_company()
        print()
        test_invalid_company()
        print()
        test_not_found()
        print()
        test_random_companies(10)
        print()
        print("=" * 50)
        print("All tests passed! Agent is ready for submission.")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
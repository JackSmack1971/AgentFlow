#!/usr/bin/env python3
"""
Security Fuzz Testing Script for AgentFlow API
"""
import atheris
import requests
import json
import sys

def fuzz_api(data):
    try:
        fdp = atheris.FuzzedDataProvider(data)

        # Fuzz various API endpoints
        endpoints = [
            "/health",
            "/auth/login",
            "/api/agents",
            "/api/search"
        ]

        for endpoint in endpoints:
            url = f"http://localhost:8000{endpoint}"

            # Generate fuzzed data
            fuzz_string = fdp.ConsumeString(100)
            fuzz_int = fdp.ConsumeInt(1000)

            if endpoint == "/auth/login":
                payload = {
                    "email": fuzz_string + "@test.com",
                    "password": fuzz_string
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, json=payload, headers=headers, timeout=5)
            else:
                params = {"q": fuzz_string, "limit": fuzz_int}
                response = requests.get(url, params=params, timeout=5)

            # Check for unexpected responses that might indicate vulnerabilities
            if response.status_code in [500, 502, 503]:
                print(f"Potential vulnerability found: {endpoint} returned {response.status_code}")

    except Exception as e:
        pass  # Ignore expected exceptions from fuzzing

if __name__ == "__main__":
    atheris.Setup(sys.argv, fuzz_api)
    atheris.Fuzz()
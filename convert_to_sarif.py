#!/usr/bin/env python3
"""
Convert Bandit JSON results to SARIF format for CI/CD integration
"""
import json
import sys
from datetime import datetime

def convert_bandit_to_sarif(bandit_json_file, sarif_output_file):
    """Convert Bandit JSON output to SARIF format"""

    with open(bandit_json_file, 'r') as f:
        bandit_data = json.load(f)

    sarif_data = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Bandit",
                        "version": "1.8.6",
                        "informationUri": "https://bandit.readthedocs.io/",
                        "rules": []
                    }
                },
                "results": []
            }
        ]
    }

    # Process each result
    for result in bandit_data.get('results', []):
        sarif_result = {
            "ruleId": result.get('test_id', 'unknown'),
            "level": result.get('issue_severity', 'warning').lower(),
            "message": {
                "text": result.get('issue_text', '')
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": result.get('filename', '')
                        },
                        "region": {
                            "startLine": result.get('line_number', 1)
                        }
                    }
                }
            ]
        }

        # Add CWE information if available
        if 'issue_cwe' in result:
            sarif_result["properties"] = {
                "cwe": result['issue_cwe'].get('id', ''),
                "confidence": result.get('issue_confidence', '')
            }

        sarif_data["runs"][0]["results"].append(sarif_result)

    # Write SARIF file
    with open(sarif_output_file, 'w') as f:
        json.dump(sarif_data, f, indent=2)

    print(f"Converted {len(sarif_data['runs'][0]['results'])} findings to SARIF format")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_to_sarif.py <bandit_json_file> <sarif_output_file>")
        sys.exit(1)

    convert_bandit_to_sarif(sys.argv[1], sys.argv[2])
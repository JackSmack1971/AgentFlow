#!/usr/bin/env python3
"""
Demonstration script for User model security enhancements.
Shows that OTP secrets are properly encrypted and security features work.
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from apps.api.app.db.models import User
from apps.api.app.utils.encryption import EncryptionManager

def main():
    print("AgentFlow User Security Enhancement Demo")
    print("=" * 50)

    # Set a test encryption key
    os.environ["FERNET_KEY"] = EncryptionManager.generate_key()

    print("\n1. Creating a test user...")
    user = User(
        email="demo@example.com",
        hashed_password="hashed_password_demo"
    )

    print("   [OK] User created successfully")
    print(f"   Email: {user.email}")
    print(f"   Failed login attempts: {user.failed_login_attempts}")
    print(f"   Account active: {user.is_active}")
    print(f"   Created at: {user.created_at}")
    print(f"   Updated at: {user.updated_at}")

    print("\n2. Setting OTP secret...")
    otp_secret = "JBSWY3DPEHPK3PXP"
    user.set_otp_secret(otp_secret)

    print(f"   Original OTP secret: {otp_secret}")
    print(f"   Encrypted in database: {user.otp_secret}")
    print(f"   Decrypted from database: {user.get_otp_secret()}")
    print(f"   Encryption working: {user.get_otp_secret() == otp_secret}")

    print("\n3. Testing account security features...")

    print("   Initial state:")
    print(f"   Failed attempts: {user.failed_login_attempts}")
    print(f"   Account locked: {user.is_account_locked()}")

    print("   Simulating failed logins...")
    for i in range(5):
        user.record_failed_login()
        print(f"   Attempt {i+1}: {user.failed_login_attempts} failed attempts")

    print(f"   Account locked after 5 failures: {user.is_account_locked()}")

    print("   Successful login resets everything...")
    user.record_successful_login()
    print(f"   Failed attempts after success: {user.failed_login_attempts}")
    print(f"   Account locked: {user.is_account_locked()}")
    print(f"   Last login: {user.last_login}")

    print("\n4. Testing soft delete...")
    print(f"   Before soft delete - is deleted: {user.is_deleted}")
    user.soft_delete()
    print(f"   After soft delete - is deleted: {user.is_deleted}")
    print(f"   After soft delete - is active: {user.is_active}")
    print(f"   Deleted at: {user.deleted_at}")

    print("\n5. Testing restore...")
    user.restore()
    print(f"   After restore - is deleted: {user.is_deleted}")
    print(f"   After restore - is active: {user.is_active}")

    print("\n" + "=" * 50)
    print("Security Enhancement Demo Complete!")
    print("\nKey Security Improvements:")
    print("- OTP secrets are encrypted in the database")
    print("- Account lockout after 5 failed attempts")
    print("- Audit timestamps (created_at, updated_at, last_login)")
    print("- Soft delete functionality")
    print("- Failed login attempt tracking")
    print("- Automatic account unlocking after successful login")

if __name__ == "__main__":
    main()
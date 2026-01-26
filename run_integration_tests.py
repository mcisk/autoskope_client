#!/usr/bin/env python3
"""Run integration tests with secure credential input.

This script prompts for credentials securely (password is hidden)
and runs the integration tests without storing credentials in shell history.

Usage:
    python run_integration_tests.py
"""

import os
import sys
import getpass
import subprocess


def main():
    """Run integration tests with secure credential input."""
    print("=" * 60)
    print("Autoskope Client - Integration Test Runner")
    print("=" * 60)
    print()

    # Check if .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"Found {env_file} file")
        use_env = input("Use credentials from .env file? [Y/n]: ").strip().lower()
        if use_env in ("", "y", "yes"):
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("✓ Loaded credentials from .env")
            except ImportError:
                print("⚠ python-dotenv not installed. Run: pip install python-dotenv")
                print("Falling back to manual input...")
                use_env = "n"
        else:
            use_env = "n"
    else:
        use_env = "n"

    # Manual input if not using .env
    if use_env == "n":
        print("\nEnter your Autoskope credentials:")
        print("(Password input will be hidden)")
        print()

        host = input("Host [https://portal.autoskope.de]: ").strip()
        if not host:
            host = "https://portal.autoskope.de"

        username = input("Username: ").strip()
        if not username:
            print("✗ Username is required")
            sys.exit(1)

        password = getpass.getpass("Password: ")
        if not password:
            print("✗ Password is required")
            sys.exit(1)

        # Set environment variables for subprocess
        os.environ["AUTOSKOPE_HOST"] = host
        os.environ["AUTOSKOPE_USERNAME"] = username
        os.environ["AUTOSKOPE_PASSWORD"] = password

    # Verify credentials are set
    if not all([
        os.getenv("AUTOSKOPE_HOST"),
        os.getenv("AUTOSKOPE_USERNAME"),
        os.getenv("AUTOSKOPE_PASSWORD"),
    ]):
        print("✗ Credentials not properly set")
        sys.exit(1)

    print()
    print("=" * 60)
    print("Running integration tests...")
    print("=" * 60)
    print()

    # Run pytest with integration tests
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_integration.py", "-v", "-s"],
        env=os.environ.copy(),
    )

    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Aborted by user")
        sys.exit(1)

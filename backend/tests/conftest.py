"""
Shared test configuration and environment setup for Complyo backend tests.
Loaded automatically by pytest before any test module.
"""

import os
import sys

# Ensure required environment variables exist before any module import
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")

# Make backend package importable from tests/ subdirectory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

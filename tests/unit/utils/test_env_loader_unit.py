"""
Unit tests for environment variables loader.
"""

import os
import pytest
from unittest.mock import patch
from z888_ai_hub.utils.env_loader import load_env

class TestEnvLoaderUnit:
    """Unit test cases for environment variables loader."""

    def test_load_env_existing(self):
        """Test loading existing environment variable."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            value = load_env('TEST_VAR')
            assert value == 'test_value'

    def test_load_env_nonexistent(self):
        """Test loading nonexistent environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            value = load_env('NONEXISTENT_VAR')
            assert value is None

    def test_load_env_empty(self):
        """Test loading empty environment variable."""
        with patch.dict(os.environ, {'EMPTY_VAR': ''}):
            value = load_env('EMPTY_VAR')
            assert value == ''

    def test_load_env_special_chars(self):
        """Test loading environment variable with special characters."""
        with patch.dict(os.environ, {'SPECIAL_VAR': 'test@#$%^&*()'}):
            value = load_env('SPECIAL_VAR')
            assert value == 'test@#$%^&*()'

    def test_load_env_unicode(self):
        """Test loading environment variable with unicode characters."""
        with patch.dict(os.environ, {'UNICODE_VAR': 'тест'}):
            value = load_env('UNICODE_VAR')
            assert value == 'тест'

    def test_load_env_case_sensitive(self):
        """Test environment variable case sensitivity."""
        with patch.dict(os.environ, {'Test_Var': 'test_value'}):
            value = load_env('TEST_VAR')
            assert value is None
            value = load_env('Test_Var')
            assert value == 'test_value' 
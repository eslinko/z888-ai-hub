"""
Integration tests for environment variables loader.
"""

import os
import pytest
from z888_ai_hub.utils.env_loader import load_env

class TestEnvLoaderIntegration:
    """Integration test cases for environment variables loader."""

    @pytest.fixture(autouse=True)
    def setup_env(self):
        """Setup test environment variables."""
        # Сохраняем текущие значения
        original_env = dict(os.environ)
        
        # Устанавливаем тестовые значения
        os.environ['TEST_VAR'] = 'test_value'
        os.environ['EMPTY_VAR'] = ''
        os.environ['SPECIAL_VAR'] = 'test@#$%^&*()'
        os.environ['UNICODE_VAR'] = 'тест'
        
        yield
        
        # Восстанавливаем оригинальные значения
        os.environ.clear()
        os.environ.update(original_env)

    def test_load_env_existing(self):
        """Test loading existing environment variable."""
        value = load_env('TEST_VAR')
        assert value == 'test_value'

    def test_load_env_empty(self):
        """Test loading empty environment variable."""
        value = load_env('EMPTY_VAR')
        assert value == ''

    def test_load_env_special_chars(self):
        """Test loading environment variable with special characters."""
        value = load_env('SPECIAL_VAR')
        assert value == 'test@#$%^&*()'

    def test_load_env_unicode(self):
        """Test loading environment variable with unicode characters."""
        value = load_env('UNICODE_VAR')
        assert value == 'тест'

    def test_load_env_nonexistent(self):
        """Test loading nonexistent environment variable."""
        value = load_env('NONEXISTENT_VAR')
        assert value is None

    def test_load_env_case_sensitive(self):
        """Test environment variable case sensitivity."""
        value = load_env('TEST_VAR')
        assert value == 'test_value'
        value = load_env('test_var')
        assert value is None

    def test_load_env_required_vars(self):
        """Test loading required environment variables."""
        # Проверяем наличие обязательных переменных окружения
        mistral_key = load_env('MISTRAL_API_KEY')
        anthropic_key = load_env('ANTHROPIC_API_KEY')
        supabase_url = load_env('SUPABASE_URL')
        supabase_key = load_env('SUPABASE_KEY')
        
        # Хотя бы одна из переменных должна быть установлена
        assert any([mistral_key, anthropic_key, supabase_url, supabase_key]), \
            "No required environment variables found" 
"""
Unit tests for configuration loader.
"""

import os
import pytest
from unittest.mock import patch, mock_open
from z888_ai_hub.config import load_config, merge_configs, validate_config


class TestConfigLoaderUnit:
    """Unit test cases for configuration loader."""

    @pytest.fixture
    def sample_config_yaml(self):
        """Sample YAML configuration."""
        return """
        connectors:
          mistral:
            api_key: ${MISTRAL_API_KEY}
            base_url: https://api.mistral.ai
            default_model: mistral-tiny
          anthropic:
            api_key: ${ANTHROPIC_API_KEY}
            default_model: claude-3-opus
        
        processing:
          max_file_size: 52428800
          max_dimensions: [1920, 1080]
          batch_size: 10
        """

    def test_load_config_with_env_vars(self, sample_config_yaml):
        """Test loading configuration with environment variables."""
        env_vars = {
            "MISTRAL_API_KEY": "test_mistral_key",
            "ANTHROPIC_API_KEY": "test_anthropic_key"
        }
        
        with patch.dict(os.environ, env_vars), \
             patch("builtins.open", mock_open(read_data=sample_config_yaml)):
            config = load_config("test_config.yaml")
            
            assert config["connectors"]["mistral"]["api_key"] == "test_mistral_key"
            assert config["connectors"]["anthropic"]["api_key"] == "test_anthropic_key"

    def test_load_config_missing_env_vars(self, sample_config_yaml):
        """Test loading configuration with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True), \
             patch("builtins.open", mock_open(read_data=sample_config_yaml)):
            config = load_config("test_config.yaml")
            
            assert config["connectors"]["mistral"]["api_key"] == "${MISTRAL_API_KEY}"
            assert config["connectors"]["anthropic"]["api_key"] == "${ANTHROPIC_API_KEY}"

    def test_load_config_invalid_yaml(self):
        """Test loading invalid YAML configuration."""
        invalid_yaml = "invalid: yaml: content: ["
        
        with patch("builtins.open", mock_open(read_data=invalid_yaml)):
            with pytest.raises(Exception, match="Invalid YAML"):
                load_config("test_config.yaml")

    def test_merge_configs(self):
        """Test merging multiple configurations."""
        base_config = {
            "connectors": {
                "mistral": {
                    "api_key": "base_key",
                    "base_url": "https://api.mistral.ai"
                }
            },
            "processing": {
                "max_file_size": 1000
            }
        }
        
        override_config = {
            "connectors": {
                "mistral": {
                    "api_key": "override_key"
                }
            },
            "processing": {
                "batch_size": 10
            }
        }
        
        merged = merge_configs(base_config, override_config)
        
        assert merged["connectors"]["mistral"]["api_key"] == "override_key"
        assert merged["connectors"]["mistral"]["base_url"] == "https://api.mistral.ai"
        assert merged["processing"]["max_file_size"] == 1000
        assert merged["processing"]["batch_size"] == 10

    def test_validate_config_required_fields(self):
        """Test configuration validation for required fields."""
        invalid_config = {
            "connectors": {
                "mistral": {
                    "base_url": "https://api.mistral.ai"
                    # Missing api_key
                }
            }
        }
        
        with pytest.raises(ValueError, match="Missing required field: api_key"):
            validate_config(invalid_config)

    def test_validate_config_field_types(self):
        """Test configuration validation for field types."""
        invalid_config = {
            "processing": {
                "max_file_size": "not_a_number",  # Should be int
                "max_dimensions": [1920, 1080]
            }
        }
        
        with pytest.raises(TypeError, match="max_file_size must be an integer"):
            validate_config(invalid_config)

    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        valid_config = {
            "connectors": {
                "mistral": {
                    "api_key": "test_key",
                    "base_url": "https://api.mistral.ai",
                    "default_model": "mistral-tiny"
                }
            },
            "processing": {
                "max_file_size": 52428800,
                "max_dimensions": [1920, 1080],
                "batch_size": 10
            }
        }
        
        # Should not raise any exceptions
        validate_config(valid_config)

    def test_load_config_nonexistent_file(self):
        """Test loading configuration from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_config("nonexistent_config.yaml")

    def test_load_config_with_includes(self, sample_config_yaml):
        """Test loading configuration with includes."""
        base_yaml = """
        include: base_config.yaml
        connectors:
          anthropic:
            api_key: override_key
        """
        
        with patch("builtins.open") as mock_file:
            mock_file.side_effect = [
                mock_open(read_data=base_yaml).return_value,
                mock_open(read_data=sample_config_yaml).return_value
            ]
            
            config = load_config("test_config.yaml")
            
            assert config["connectors"]["anthropic"]["api_key"] == "override_key"
            assert "mistral" in config["connectors"] 
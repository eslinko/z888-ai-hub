"""
Integration tests for configuration loader.
"""

import os
import pytest
import tempfile
import yaml
from z888_ai_hub.config import load_config, merge_configs, validate_config


class TestConfigLoaderIntegration:
    """Integration test cases for configuration loader."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for test config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def base_config_file(self, temp_config_dir):
        """Create a base config file for testing."""
        config_path = os.path.join(temp_config_dir, "base_config.yaml")
        config_data = {
            "api": {
                "base_url": "https://api.example.com",
                "version": "v1",
                "timeout": 30
            },
            "connectors": {
                "mistral": {
                    "model": "mistral-tiny",
                    "temperature": 0.7
                },
                "anthropic": {
                    "model": "claude-3-opus",
                    "temperature": 0.8
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        return config_path

    @pytest.fixture
    def env_config_file(self, temp_config_dir):
        """Create an environment-specific config file."""
        config_path = os.path.join(temp_config_dir, "env_config.yaml")
        config_data = {
            "api": {
                "base_url": "https://staging.example.com",
                "timeout": 60
            },
            "connectors": {
                "mistral": {
                    "temperature": 0.9
                }
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        return config_path

    def test_load_real_config_file(self, base_config_file):
        """Test loading a real configuration file."""
        config = load_config(base_config_file)
        
        assert isinstance(config, dict)
        assert "api" in config
        assert "connectors" in config
        assert "logging" in config
        
        assert config["api"]["base_url"] == "https://api.example.com"
        assert config["connectors"]["mistral"]["model"] == "mistral-tiny"
        assert config["logging"]["level"] == "INFO"

    def test_merge_real_configs(self, base_config_file, env_config_file):
        """Test merging multiple real configuration files."""
        base_config = load_config(base_config_file)
        env_config = load_config(env_config_file)
        
        merged_config = merge_configs(base_config, env_config)
        
        # Check that env config values override base config
        assert merged_config["api"]["base_url"] == "https://staging.example.com"
        assert merged_config["api"]["timeout"] == 60
        assert merged_config["connectors"]["mistral"]["temperature"] == 0.9
        assert merged_config["logging"]["level"] == "DEBUG"
        
        # Check that non-overridden values remain
        assert merged_config["api"]["version"] == "v1"
        assert merged_config["connectors"]["mistral"]["model"] == "mistral-tiny"
        assert merged_config["connectors"]["anthropic"]["model"] == "claude-3-opus"

    def test_load_config_with_env_vars(self, base_config_file):
        """Test loading config with real environment variables."""
        # Set environment variables
        os.environ["API_BASE_URL"] = "https://prod.example.com"
        os.environ["MISTRAL_MODEL"] = "mistral-medium"
        
        config = load_config(base_config_file)
        
        assert config["api"]["base_url"] == "https://prod.example.com"
        assert config["connectors"]["mistral"]["model"] == "mistral-medium"
        
        # Clean up environment
        del os.environ["API_BASE_URL"]
        del os.environ["MISTRAL_MODEL"]

    def test_config_file_modifications(self, base_config_file):
        """Test handling of configuration file modifications."""
        # Load initial config
        initial_config = load_config(base_config_file)
        
        # Modify the config file
        with open(base_config_file, "r") as f:
            config_data = yaml.safe_load(f)
        
        config_data["api"]["timeout"] = 45
        config_data["connectors"]["mistral"]["temperature"] = 0.5
        
        with open(base_config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Load modified config
        modified_config = load_config(base_config_file)
        
        assert modified_config["api"]["timeout"] == 45
        assert modified_config["connectors"]["mistral"]["temperature"] == 0.5
        assert modified_config != initial_config

    def test_validate_real_config(self, base_config_file):
        """Test validation with a real configuration."""
        config = load_config(base_config_file)
        
        # Should not raise any exceptions
        validate_config(config)
        
        # Test with invalid config
        invalid_config = config.copy()
        del invalid_config["api"]["base_url"]
        
        with pytest.raises(Exception):
            validate_config(invalid_config)

    def test_config_with_includes(self, temp_config_dir):
        """Test loading configuration with includes."""
        # Create included config
        included_config_path = os.path.join(temp_config_dir, "included.yaml")
        included_data = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "testdb"
            }
        }
        
        with open(included_config_path, "w") as f:
            yaml.dump(included_data, f)
        
        # Create main config with include
        main_config_path = os.path.join(temp_config_dir, "main.yaml")
        main_data = {
            "include": ["included.yaml"],
            "api": {
                "port": 8080
            }
        }
        
        with open(main_config_path, "w") as f:
            yaml.dump(main_data, f)
        
        # Load and verify
        config = load_config(main_config_path)
        
        assert "database" in config
        assert config["database"]["host"] == "localhost"
        assert config["api"]["port"] == 8080

    def test_config_reload(self, base_config_file):
        """Test configuration reloading."""
        # Initial load
        initial_config = load_config(base_config_file)
        
        # Modify config file
        with open(base_config_file, "r") as f:
            config_data = yaml.safe_load(f)
        
        config_data["api"]["version"] = "v2"
        
        with open(base_config_file, "w") as f:
            yaml.dump(config_data, f)
        
        # Reload config
        reloaded_config = load_config(base_config_file)
        
        assert reloaded_config["api"]["version"] == "v2"
        assert reloaded_config != initial_config

    def test_config_with_defaults(self, temp_config_dir):
        """Test configuration with default values."""
        config_path = os.path.join(temp_config_dir, "minimal_config.yaml")
        minimal_data = {
            "api": {
                "base_url": "https://api.example.com"
            }
        }
        
        with open(config_path, "w") as f:
            yaml.dump(minimal_data, f)
        
        config = load_config(config_path)
        
        # Check that default values are applied
        assert "timeout" in config["api"]
        assert isinstance(config["api"]["timeout"], int)
        assert "logging" in config
        assert "level" in config["logging"] 
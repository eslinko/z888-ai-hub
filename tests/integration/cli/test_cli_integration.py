"""
Integration tests for CLI functionality.
"""

import os
import pytest
import tempfile
import json
from pathlib import Path
from z888_ai_hub.cli import process_directory
from z888_ai_hub.connectors.mistral import MistralConnector

class TestCLIIntegration:
    """Integration test cases for CLI functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield Path(tmpdirname)

    @pytest.fixture
    def sample_config(self, temp_dir):
        """Create sample configuration file."""
        config = {
            "connectors": {
                "mistral": {
                    "api_key": "test_key",
                    "base_url": "https://api.mistral.ai",
                    "default_model": "mistral-tiny"
                }
            },
            "ocr": {
                "enabled": True,
                "provider": "mistral",
                "model": "mistral-tiny"
            },
            "parsing": {
                "max_image_size": 4096,
                "image_quality": 85,
                "batch_size": 10
            }
        }
        
        config_path = temp_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return config_path

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample files for testing."""
        # Create test PDF
        pdf_path = temp_dir / "test.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(b'%PDF-1.4\n%Test PDF content')
        
        # Create test DOC
        doc_path = temp_dir / "test.doc"
        with open(doc_path, 'wb') as f:
            f.write(b'PK\x03\x04\x14\x00\x00\x00\x08\x00Test DOC content')
        
        return {
            'pdf': pdf_path,
            'doc': doc_path
        }

    @pytest.mark.asyncio
    async def test_process_directory_with_config(self, temp_dir, sample_config, sample_files):
        """Test processing directory with configuration file."""
        result = await process_directory(
            input_dir=str(temp_dir),
            output_dir=str(temp_dir / "output"),
            config_path=str(sample_config)
        )
        
        assert result.success
        assert result.total_files == 2
        assert result.processed_files > 0
        assert (temp_dir / "output").exists()

    @pytest.mark.asyncio
    async def test_process_directory_without_config(self, temp_dir, sample_files):
        """Test processing directory without configuration file."""
        result = await process_directory(
            input_dir=str(temp_dir),
            output_dir=str(temp_dir / "output")
        )
        
        assert result.success
        assert result.total_files == 2
        assert result.processed_files > 0
        assert (temp_dir / "output").exists()

    @pytest.mark.asyncio
    async def test_process_directory_with_nonexistent_dir(self, temp_dir):
        """Test processing directory with nonexistent input directory."""
        with pytest.raises(FileNotFoundError):
            await process_directory(
                input_dir=str(temp_dir / "nonexistent"),
                output_dir=str(temp_dir / "output")
            )

    @pytest.mark.asyncio
    async def test_process_directory_with_invalid_config(self, temp_dir, sample_files):
        """Test processing directory with invalid configuration file."""
        invalid_config = temp_dir / "invalid_config.json"
        with open(invalid_config, 'w') as f:
            f.write('{"invalid": "json"')
        
        with pytest.raises(json.JSONDecodeError):
            await process_directory(
                input_dir=str(temp_dir),
                output_dir=str(temp_dir / "output"),
                config_path=str(invalid_config)
            ) 
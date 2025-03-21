"""
Unit tests for connector registry.
"""

import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.registry.connector_registry import ConnectorRegistry
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability


class TestConnectorRegistryUnit:
    """Unit test cases for connector registry."""

    @pytest.fixture
    def mock_connector(self):
        """Create a mock connector."""
        mock = Mock(spec=BaseConnector)
        mock.capabilities = [ConnectorCapability.OCR]
        return mock

    @pytest.fixture
    def registry(self):
        """Create a clean registry instance."""
        return ConnectorRegistry()

    def test_register_connector(self, registry, mock_connector):
        """Test registering a connector."""
        registry.register("test", mock_connector)
        assert registry.get("test") == mock_connector

    def test_register_duplicate_connector(self, registry, mock_connector):
        """Test registering a connector with duplicate name."""
        registry.register("test", mock_connector)
        with pytest.raises(ValueError, match="Connector 'test' is already registered"):
            registry.register("test", mock_connector)

    def test_get_nonexistent_connector(self, registry):
        """Test getting a nonexistent connector."""
        with pytest.raises(KeyError, match="Connector 'nonexistent' not found"):
            registry.get("nonexistent")

    def test_get_all_connectors(self, registry, mock_connector):
        """Test getting all registered connectors."""
        registry.register("test1", mock_connector)
        mock_connector2 = Mock(spec=BaseConnector)
        registry.register("test2", mock_connector2)

        connectors = registry.get_all()
        assert len(connectors) == 2
        assert "test1" in connectors
        assert "test2" in connectors

    def test_get_connectors_by_capability(self, registry, mock_connector):
        """Test getting connectors by capability."""
        registry.register("ocr", mock_connector)
        
        # Create connector without OCR capability
        mock_connector2 = Mock(spec=BaseConnector)
        mock_connector2.capabilities = [ConnectorCapability.TEXT]
        registry.register("text", mock_connector2)

        ocr_connectors = registry.get_by_capability(ConnectorCapability.OCR)
        assert len(ocr_connectors) == 1
        assert "ocr" in ocr_connectors

        text_connectors = registry.get_by_capability(ConnectorCapability.TEXT)
        assert len(text_connectors) == 1
        assert "text" in text_connectors

    def test_remove_connector(self, registry, mock_connector):
        """Test removing a connector."""
        registry.register("test", mock_connector)
        registry.remove("test")
        
        with pytest.raises(KeyError):
            registry.get("test")

    def test_remove_nonexistent_connector(self, registry):
        """Test removing a nonexistent connector."""
        with pytest.raises(KeyError, match="Connector 'nonexistent' not found"):
            registry.remove("nonexistent")

    def test_clear_registry(self, registry, mock_connector):
        """Test clearing all connectors from registry."""
        registry.register("test1", mock_connector)
        registry.register("test2", Mock(spec=BaseConnector))
        
        registry.clear()
        assert len(registry.get_all()) == 0

    def test_connector_validation(self, registry):
        """Test connector validation during registration."""
        invalid_connector = Mock()  # Not a BaseConnector
        
        with pytest.raises(TypeError, match="Connector must be an instance of BaseConnector"):
            registry.register("invalid", invalid_connector)

    def test_registry_singleton(self):
        """Test that registry behaves like a singleton."""
        registry1 = ConnectorRegistry()
        registry2 = ConnectorRegistry()
        
        mock_connector = Mock(spec=BaseConnector)
        registry1.register("test", mock_connector)
        
        assert registry2.get("test") == mock_connector 
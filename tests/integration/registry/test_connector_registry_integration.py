"""
Integration tests for connector registry.
"""

import pytest
from z888_ai_hub.registry.connector_registry import ConnectorRegistry
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.base_connector import ConnectorCapability


class TestConnectorRegistryIntegration:
    """Integration test cases for connector registry."""

    @pytest.fixture
    def mistral_connector(self):
        """Create a real Mistral connector."""
        return MistralConnector(
            api_key="test_key",
            base_url="https://api.mistral.ai",
            default_model="mistral-tiny"
        )

    @pytest.fixture
    def anthropic_connector(self):
        """Create a real Anthropic connector."""
        return AnthropicConnector(
            api_key="test_key",
            default_model="claude-3-opus"
        )

    @pytest.fixture
    def registry(self):
        """Create a clean registry instance."""
        registry = ConnectorRegistry()
        registry.clear()  # Ensure clean state
        return registry

    def test_register_real_connectors(self, registry, mistral_connector, anthropic_connector):
        """Test registering real connectors."""
        registry.register("mistral", mistral_connector)
        registry.register("anthropic", anthropic_connector)

        assert isinstance(registry.get("mistral"), MistralConnector)
        assert isinstance(registry.get("anthropic"), AnthropicConnector)

    def test_connector_capabilities(self, registry, mistral_connector, anthropic_connector):
        """Test getting connectors by real capabilities."""
        registry.register("mistral", mistral_connector)
        registry.register("anthropic", anthropic_connector)

        text_connectors = registry.get_by_capability(ConnectorCapability.TEXT)
        assert len(text_connectors) == 2  # Both support TEXT
        assert "mistral" in text_connectors
        assert "anthropic" in text_connectors

        ocr_connectors = registry.get_by_capability(ConnectorCapability.OCR)
        assert len(ocr_connectors) == 1  # Only Mistral supports OCR
        assert "mistral" in ocr_connectors

    def test_registry_persistence(self, mistral_connector):
        """Test registry state persistence across instances."""
        # First registry instance
        registry1 = ConnectorRegistry()
        registry1.register("mistral", mistral_connector)

        # Second registry instance
        registry2 = ConnectorRegistry()
        assert isinstance(registry2.get("mistral"), MistralConnector)
        assert registry2.get("mistral").api_key == "test_key"
        assert registry2.get("mistral").default_model == "mistral-tiny"

    def test_connector_configuration(self, registry, mistral_connector):
        """Test connector configuration preservation."""
        registry.register("mistral", mistral_connector)
        retrieved = registry.get("mistral")

        assert retrieved.api_key == "test_key"
        assert retrieved.base_url == "https://api.mistral.ai"
        assert retrieved.default_model == "mistral-tiny"

    def test_multiple_connector_operations(self, registry, mistral_connector, anthropic_connector):
        """Test multiple operations with real connectors."""
        # Register connectors
        registry.register("mistral", mistral_connector)
        registry.register("anthropic", anthropic_connector)
        assert len(registry.get_all()) == 2

        # Remove one connector
        registry.remove("mistral")
        assert len(registry.get_all()) == 1
        assert "anthropic" in registry.get_all()

        # Clear registry
        registry.clear()
        assert len(registry.get_all()) == 0

    @pytest.mark.asyncio
    async def test_connector_functionality(self, registry, mistral_connector):
        """Test that registered connector maintains its functionality."""
        registry.register("mistral", mistral_connector)
        connector = registry.get("mistral")

        # Test that connector's methods are preserved
        assert hasattr(connector, "process")
        assert hasattr(connector, "extract_text")
        assert connector.capabilities == mistral_connector.capabilities

    def test_registry_thread_safety(self, registry, mistral_connector, anthropic_connector):
        """Test registry operations from multiple threads."""
        import threading
        import queue

        results = queue.Queue()

        def worker(name, connector):
            try:
                registry.register(name, connector)
                retrieved = registry.get(name)
                results.put((name, isinstance(retrieved, type(connector))))
            except Exception as e:
                results.put((name, e))

        # Create threads
        thread1 = threading.Thread(target=worker, args=("mistral", mistral_connector))
        thread2 = threading.Thread(target=worker, args=("anthropic", anthropic_connector))

        # Start threads
        thread1.start()
        thread2.start()

        # Wait for threads to complete
        thread1.join()
        thread2.join()

        # Check results
        while not results.empty():
            name, success = results.get()
            assert success, f"Thread operation failed for {name}"

        # Verify final state
        assert len(registry.get_all()) == 2
        assert isinstance(registry.get("mistral"), MistralConnector)
        assert isinstance(registry.get("anthropic"), AnthropicConnector) 
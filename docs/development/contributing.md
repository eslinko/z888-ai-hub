# Contributing Guide

Thank you for your interest in contributing to Z888 AI Hub! This guide will help you get started.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/z888-ai-hub.git
   cd z888-ai-hub
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Run tests:
   ```bash
   pytest
   ```
4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```
5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
6. Create a pull request

## Code Style

We follow PEP 8 guidelines:

### Indentation
- Use 4 spaces for indentation
- No tabs

### Line Length
- Maximum line length: 88 characters
- Use line continuation for long lines

### Variable Naming
- Use snake_case for functions and variables
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Docstrings
- Use Google style docstrings
- Include type hints
- Document exceptions

Example:
```python
def process_request(
    self,
    prompt: str,
    model: Optional[str] = None,
    **kwargs
) -> str:
    """Process a single request to the AI service.

    Args:
        prompt: Text prompt for the AI service
        model: Model to use (optional)
        **kwargs: Additional parameters

    Returns:
        Generated text response

    Raises:
        AIError: If the request fails
        ValueError: If parameters are invalid
    """
    pass
```

## Testing

### Directory Structure
```
tests/
├── unit/
│   ├── client/
│   ├── connectors/
│   └── utils/
└── integration/
    ├── client/
    ├── connectors/
    └── utils/
```

### Naming Conventions
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

Example:
```python
import pytest
from z888_ai_hub import AIClient

class TestAIClient:
    @pytest.fixture
    def client(self):
        return AIClient(
            connector_name="mistral",
            api_key="test-key"
        )

    async def test_process_request(self, client):
        response = await client.process_request(
            prompt="Test prompt"
        )
        assert response is not None
        assert isinstance(response, str)
```

## Documentation

### Writing Documentation
1. Update relevant .md files
2. Add docstrings to new code
3. Update examples if needed
4. Build documentation:
   ```bash
   make html
   ```

### Documentation Structure
```
docs/
├── api.md
├── configuration.md
├── examples.md
├── installation.md
├── usage/
│   ├── quickstart.md
│   └── advanced.md
└── development/
    ├── contributing.md
    └── testing.md
```

## Creating New Connectors

1. Create connector class:
   ```python
   from z888_ai_hub import BaseConnector

   class CustomConnector(BaseConnector):
       async def process_request(
           self,
           prompt: str,
           model: Optional[str] = None,
           **kwargs
       ) -> str:
           # Implementation
           pass

       def validate_config(self, config: Dict[str, Any]) -> None:
           # Validation
           pass
   ```

2. Add tests:
   ```python
   class TestCustomConnector:
       @pytest.fixture
       def connector(self):
           return CustomConnector(
               api_key="test-key",
               base_url="http://test-api"
           )

       async def test_process_request(self, connector):
           response = await connector.process_request(
               prompt="Test prompt"
           )
           assert response is not None
   ```

3. Update documentation:
   - Add to connectors/README.md
   - Update examples
   - Add API documentation

## Pull Request Process

1. Update CHANGELOG.md
2. Add tests for new features
3. Ensure all tests pass
4. Create pull request with:
   - Description of changes
   - Related issues
   - Breaking changes
   - New dependencies

## Code Review

Pull requests are reviewed for:
- Code quality
- Test coverage
- Documentation
- Performance
- Security

## Getting Help

- Check existing issues
- Ask in pull requests
- Join community chat

## Release Process

1. Update version in setup.py
2. Create release notes
3. Tag the release
4. Publish to PyPI

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 
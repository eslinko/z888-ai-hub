# Contributing to Z888 AI Hub

Thank you for your interest in contributing to Z888 AI Hub! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/z888-ai-hub.git
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

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Keep functions focused and small
- Write docstrings for all public APIs
- Use meaningful variable and function names

### Running Style Checks

```bash
# Run flake8
flake8

# Run mypy
mypy src/z888_ai_hub
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_client.py

# Run with coverage report
pytest --cov=z888_ai_hub
```

### Writing Tests

- Write unit tests for new functionality
- Include edge cases and error conditions
- Mock external API calls
- Use fixtures for common test data
- Follow the Arrange-Act-Assert pattern

## Documentation

### Updating Documentation

- Keep documentation up to date with code changes
- Update API reference for new/changed methods
- Add examples for new features
- Update configuration examples if needed
- Document breaking changes

### Documentation Structure

- `docs/api.md`: API reference
- `docs/configuration.md`: Configuration guide
- `docs/installation.md`: Installation guide
- `docs/Technical Architecture.md`: Technical architecture

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes:
   - Write code
   - Add tests
   - Update documentation
   - Run style checks and tests

3. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

4. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

5. Create a Pull Request:
   - Use a clear title
   - Describe your changes
   - Link related issues
   - Include test results

## Code Review Guidelines

### For Contributors

- Keep PRs focused and small
- Respond to review comments promptly
- Update PR based on feedback
- Ensure all checks pass

### For Reviewers

- Review code style and quality
- Check test coverage
- Verify documentation updates
- Test the changes locally

## Release Process

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create a release branch
4. Run full test suite
5. Create a release tag
6. Push to PyPI

## Getting Help

- Check [GitHub Issues](https://github.com/yourusername/z888-ai-hub/issues)
- Ask questions in issues
- Join discussions in pull requests

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License. 
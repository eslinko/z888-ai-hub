# Z888 AI Hub

A Python library for interacting with various AI services, providing a unified interface for text generation, summarization, classification, and OCR capabilities.

## Features

- **Multiple AI Providers**
  - Mistral AI
  - Anthropic (Claude)
  
- **Core Capabilities**
  - Text Generation
  - Text Summarization
  - Text Classification
  - OCR (Optical Character Recognition)

- **Flexible Configuration**
  - YAML-based configuration
  - Environment variable support
  - Environment-specific settings

## Installation

### Using pip

```bash
pip install z888-ai-hub
```

### From Source

```bash
git clone https://github.com/yourusername/z888-ai-hub.git
cd z888-ai-hub
pip install -e .
```

## Quick Start

1. Set up environment variables:

```env
# Mistral AI
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_BASE_URL=https://api.mistral.ai/v1

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1
```

2. Create a configuration file (`config/config.yaml`):

```yaml
api:
  base_url: "https://api.mistral.ai/v1"
  timeout: 30
  max_retries: 3

connectors:
  mistral:
    type: "mistral"
    api_key: "${MISTRAL_API_KEY}"
    base_url: "${MISTRAL_BASE_URL}"
    default_model: "mistral-large"
    capabilities:
      text_generation:
        enabled: true
      ocr:
        enabled: true
  
  anthropic:
    type: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "${ANTHROPIC_BASE_URL}"
    default_model: "claude-3-opus"
    capabilities:
      text_generation:
        enabled: true
      summarization:
        enabled: true
```

3. Use the library:

```python
from z888_ai_hub import AIClient

async def main():
    client = AIClient(config_path="config/config.yaml")
    
    # Generate text
    response = await client.generate_text("Hello, world!")
    print("Generated text:", response)
    
    # Summarize text
    summary = await client.summarize_text("This is a long text that needs to be summarized...")
    print("Summary:", summary)
    
    # Classify text
    category = await client.classify_text("This is a positive review", ["positive", "negative"])
    print("Category:", category)
    
    # Extract text from image
    text = await client.extract_text_from_image("path/to/image.png")
    print("Extracted text:", text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Documentation

- [API Reference](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Installation Guide](docs/installation.md)
- [Technical Architecture](docs/Technical%20Architecture.md)

## Development

### Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Running Tests

```bash
pytest
```

### Code Style

The project follows PEP 8 guidelines. Run the following to check:

```bash
flake8
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- Check [GitHub Issues](https://github.com/yourusername/z888-ai-hub/issues)
- Create a new issue with:
  - Your Python version
  - Installation method
  - Error message
  - Steps to reproduce

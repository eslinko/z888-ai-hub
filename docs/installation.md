# Installation Guide

## System Requirements

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

## Installation Methods

### Using pip

```bash
pip install z888-ai-hub
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/z888-ai-hub.git
cd z888-ai-hub

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

## Environment Setup

### Required Environment Variables

Create a `.env` file in your project root:

```env
# Mistral AI
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_BASE_URL=https://api.mistral.ai/v1

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1

# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

## Configuration

Create a configuration file (e.g., `config/config.yaml`):

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

tasks:
  text_generation:
    provider: "anthropic"
    model: "claude-3-opus"
    parameters:
      max_tokens: 1000
      temperature: 0.7
  
  summarization:
    provider: "mistral"
    model: "mistral-large"
    parameters:
      max_length: 500
```

## Verification

Test your installation:

```python
from z888_ai_hub import AIClient

async def test_connection():
    client = AIClient(config_path="config/config.yaml")
    
    # Test text generation
    response = await client.generate_text("Hello, world!")
    print("Text generation:", response)
    
    # Test summarization
    summary = await client.summarize_text("This is a long text that needs to be summarized...")
    print("Summarization:", summary)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_connection())
```

## Troubleshooting

### Common Issues

1. Import Error
   ```bash
   ModuleNotFoundError: No module named 'z888_ai_hub'
   ```
   Solution: Make sure you've installed the package and activated your virtual environment.

2. API Key Error
   ```bash
   ValueError: Missing API key
   ```
   Solution: Set the required environment variables or provide the API key in the configuration file.

3. Configuration Error
   ```bash
   ConfigError: Invalid configuration format
   ```
   Solution: Check your YAML configuration file syntax and required fields.

4. Connection Error
   ```bash
   ConnectionError: Failed to connect to API
   ```
   Solution: Check your internet connection and API endpoint configuration.

### Getting Help

- Check [GitHub Issues](https://github.com/yourusername/z888-ai-hub/issues)
- Create a new issue with:
  - Your Python version
  - Installation method
  - Error message
  - Steps to reproduce

## Development Installation

For development work:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## Updating

```bash
pip install --upgrade z888-ai-hub
```

## Uninstallation

```bash
pip uninstall z888-ai-hub
``` 
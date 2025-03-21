# Quick Start Guide

## Basic Usage

### 1. Installation

```bash
pip install z888-ai-hub
```

### 2. Environment Setup

Create a `.env` file:

```env
MISTRAL_API_KEY=your_mistral_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 3. Configuration

Create `config.yaml`:

```yaml
services:
  mistral:
    api_key: ${MISTRAL_API_KEY}
    model: mistral-tiny
    max_tokens: 1000
    temperature: 0.7

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus-20240229
    max_tokens: 1000
    temperature: 0.7

connectors:
  mistral:
    enabled: true
    capabilities:
      - text_generation
      - text_summarization
    default_model: mistral-tiny

  anthropic:
    enabled: true
    capabilities:
      - text_generation
      - text_classification
    default_model: claude-3-opus-20240229
```

### 4. Basic Example

```python
import asyncio
from z888_ai_hub import AIClient

async def main():
    # Initialize client
    client = AIClient("config.yaml")
    
    # Generate text
    text = await client.generate_text("Write a short story about a robot")
    print("Generated text:", text)
    
    # Summarize text
    summary = await client.summarize_text("Long article text...")
    print("Summary:", summary)
    
    # Classify text
    category = await client.classify_text(
        "This product is amazing!",
        categories=["positive", "negative", "neutral"]
    )
    print("Category:", category)

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Usage

### 1. Custom Parameters

```python
# Generate text with custom parameters
text = await client.generate_text(
    "Write a story",
    connector_name="mistral",
    max_tokens=2000,
    temperature=0.8
)

# Summarize with custom parameters
summary = await client.summarize_text(
    "Long text...",
    connector_name="mistral",
    max_tokens=300,
    temperature=0.5
)

# Classify with custom parameters
category = await client.classify_text(
    "Review text...",
    categories=["good", "bad", "neutral"],
    connector_name="anthropic",
    temperature=0.2
)
```

### 2. Error Handling

```python
from z888_ai_hub import Z888AIError, ConfigurationError, ConnectorError

async def safe_api_call():
    try:
        client = AIClient("config.yaml")
        result = await client.generate_text("Hello")
        print(result)
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
    except ConnectorError as e:
        print(f"API error: {e}")
    except Z888AIError as e:
        print(f"General error: {e}")
```

### 3. Using Different Connectors

```python
# Use Mistral for text generation
text = await client.generate_text(
    "Write a story",
    connector_name="mistral"
)

# Use Anthropic for classification
category = await client.classify_text(
    "Review text...",
    categories=["good", "bad"],
    connector_name="anthropic"
)
```

## Best Practices

1. **Environment Variables**
   - Always use environment variables for sensitive data
   - Never commit API keys to version control

2. **Configuration**
   - Keep configuration files separate for different environments
   - Use meaningful names for configuration files

3. **Error Handling**
   - Always implement proper error handling
   - Log errors for debugging

4. **Resource Management**
   - Use async/await properly
   - Close connections when done

## Next Steps

1. Read the [API Reference](../api.md) for detailed documentation
2. Check the [Configuration Guide](../configuration.md) for advanced settings
3. Look at the [Technical Architecture](../Technical%20Architecture.md) for system design
4. Visit [GitHub](https://github.com/yourusername/z888-ai-hub) for updates and issues

## Getting Help

- Check [GitHub Issues](https://github.com/yourusername/z888-ai-hub/issues)
- Review the [API Documentation](../api.md)
- Join our [Discord Community](https://discord.gg/your-server) 
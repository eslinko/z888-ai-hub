# Examples

This guide provides practical examples of using the Z888 AI Hub library for various AI tasks.

## Basic Usage

### Text Generation

```python
from z888_ai_hub.client import AIClient

# Initialize client
client = AIClient()

# Generate text
response = await client.generate_text(
    prompt="Write a short story about a robot learning to paint"
)
print(response)
```

### Text Summarization

```python
from z888_ai_hub.client import AIClient

# Initialize client
client = AIClient()

# Summarize text
text = """
The Z888 AI Hub is a powerful library that provides a unified interface for working with various AI services.
It supports multiple providers like Mistral and Anthropic, offering capabilities such as text generation,
summarization, classification, and more. The library is designed to be easy to use while providing advanced
features for complex AI tasks.
"""

summary = await client.summarize_text(
    text=text,
    max_length=280  # Default value
)
print(summary)
```

### Text Classification

```python
from z888_ai_hub.client import AIClient

# Initialize client
client = AIClient()

# Classify text
text = "The movie was absolutely fantastic! The acting was superb and the plot was engaging."
labels = ["positive", "negative", "neutral"]

result = client.classify_text(  # Note: synchronous method
    text=text,
    labels=labels
)
print(f"Classification: {result}")
```

### OCR (Text Extraction from Images)

```python
from z888_ai_hub.client import AIClient
from z888_ai_hub.exceptions import ConnectorError

# Initialize client
client = AIClient()

try:
    # Extract text from image
    text = await client.extract_text_from_image(
        image_path="path/to/image.jpg"
    )
    print(text)
except ConnectorError as e:
    print(f"OCR not supported by current connector: {e}")
except FileNotFoundError as e:
    print(f"Image file not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Advanced Usage

### Using Specific Connectors

```python
from z888_ai_hub.client import AIClient

# Initialize client with specific connector
client = AIClient(connector_name="mistral")  # or "anthropic"

# Generate text using Mistral
response = await client.generate_text(
    prompt="Explain quantum computing in simple terms"
)
print(response)

# Note: OCR is only supported by Mistral connector
try:
    text = await client.extract_text_from_image("image.jpg")
    print(text)
except NotImplementedError:
    print("OCR not supported by this connector")
```

### Custom Configuration

```python
from z888_ai_hub.client import AIClient
from z888_ai_hub.config import load_config

# Load custom configuration
config = load_config("config/custom_config.yaml")

# Initialize client with custom config
client = AIClient(config_path="config/custom_config.yaml")

# Use client with custom settings
response = await client.generate_text(
    prompt="Write a poem about artificial intelligence"
)
print(response)
```

### Error Handling

```python
from z888_ai_hub.client import AIClient
from z888_ai_hub.exceptions import (
    ConnectorError,
    ProcessingError,
    ConfigurationError,
    StorageError
)

# Initialize client
client = AIClient()

try:
    # Attempt text generation
    response = await client.generate_text(
        prompt="Generate a creative story"
    )
    print(response)
except ConnectorError as e:
    print(f"Connection error: {e}")
except ProcessingError as e:
    print(f"Processing error: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except StorageError as e:
    print(f"Storage error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Batch Processing

```python
from z888_ai_hub.client import AIClient
import asyncio

# Initialize client
client = AIClient()

# List of texts to process
texts = [
    "First text to summarize",
    "Second text to summarize",
    "Third text to summarize"
]

# Process texts concurrently
async def process_texts():
    tasks = [
        client.summarize_text(text, max_length=280)
        for text in texts
    ]
    results = await asyncio.gather(*tasks)
    return results

# Run batch processing
summaries = await process_texts()
for text, summary in zip(texts, summaries):
    print(f"Original: {text[:50]}...")
    print(f"Summary: {summary}\n")
```

### Document Processing

```python
from z888_ai_hub.client import AIClient
from z888_ai_hub.processors import PDFProcessor

# Initialize client and processor
client = AIClient()
processor = PDFProcessor()

# Process PDF document
async def process_document():
    # Extract text from PDF
    text = await processor.extract_text("document.pdf")
    
    # Generate summary
    summary = await client.summarize_text(text)
    
    # Classify content
    classification = client.classify_text(  # Note: synchronous method
        text=text,
        labels=["technical", "business", "legal"]
    )
    
    return {
        "summary": summary,
        "classification": classification
    }

# Process document
result = await process_document()
print(f"Summary: {result['summary']}")
print(f"Classification: {result['classification']}")
```

### Storage Integration

```python
from z888_ai_hub.client import AIClient
from z888_ai_hub.storage import DocumentStorage

# Initialize client and storage
client = AIClient()
storage = DocumentStorage()

# Process and store document
async def process_and_store():
    # Generate content
    content = await client.generate_text(
        prompt="Write a technical specification"
    )
    
    # Store document
    doc_id = await storage.store_document({
        "content": content,
        "metadata": {
            "type": "specification",
            "generated_by": "ai"
        }
    })
    
    return doc_id

# Process and store
doc_id = await process_and_store()
print(f"Document stored with ID: {doc_id}")

# Retrieve document
document = await storage.get_document(doc_id)
print(f"Retrieved document: {document['content'][:200]}...")
```

## Best Practices

1. **Resource Management**
   ```python
   # Use async context manager
   async with AIClient() as client:
       response = await client.generate_text(prompt="Hello")
   ```

2. **Configuration Management**
   ```python
   # Load configuration once
   config = load_config("config/base_config.yaml")
   
   # Use the same config for multiple clients
   client1 = AIClient(config=config)
   client2 = AIClient(config=config)
   ```

3. **Error Recovery**
   ```python
   # Implement retry logic
   async def generate_with_retry(prompt, max_retries=3):
       for attempt in range(max_retries):
           try:
               return await client.generate_text(prompt)
           except ConnectorError:
               if attempt == max_retries - 1:
                   raise
               await asyncio.sleep(2 ** attempt)
   ```

4. **Batch Processing**
   ```python
   # Process in chunks to avoid overwhelming the API
   async def process_in_chunks(items, chunk_size=10):
       for i in range(0, len(items), chunk_size):
           chunk = items[i:i + chunk_size]
           tasks = [process_item(item) for item in chunk]
           await asyncio.gather(*tasks)
   ```

## Getting Help

For more examples and use cases:
- Check the [API Reference](api.md)
- Visit the [GitHub Repository](https://github.com/yourusername/z888-ai-hub)
- Join our [Discord Community](https://discord.gg/your-server) 
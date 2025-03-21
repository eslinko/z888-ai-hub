# API Reference

## AIClient

Main class for interacting with AI services.

### Constructor

```python
client = AIClient(config_path: str)
```

Parameters:
- `config_path` (str): Path to YAML configuration file

### Methods

#### generate_text

```python
async def generate_text(self, prompt: str) -> str
```

Generates text using the AI model.

Parameters:
- `prompt` (str): Input prompt text

Returns:
- str: Generated text

#### summarize_text

```python
async def summarize_text(self, text: str, max_length: int = 500) -> str
```

Creates a summary of the input text.

Parameters:
- `text` (str): Input text to summarize
- `max_length` (int, optional): Maximum length of the summary. Defaults to 500.

Returns:
- str: Summarized text

#### classify_text

```python
async def classify_text(self, text: str, categories: List[str]) -> str
```

Classifies text into predefined categories.

Parameters:
- `text` (str): Text to classify
- `categories` (List[str]): List of possible categories

Returns:
- str: Determined category

#### extract_text_from_image

```python
async def extract_text_from_image(self, image_path: str) -> str
```

Extracts text from an image using OCR.

Parameters:
- `image_path` (str): Path to the image file

Returns:
- str: Extracted text

## ConnectorRegistry

Registry for managing available connectors.

### Methods

#### register_connector

```python
def register_connector(self, connector: BaseConnector) -> None
```

Registers a new connector.

Parameters:
- `connector` (BaseConnector): Connector instance

#### get_connector

```python
def get_connector(self, name: str) -> BaseConnector
```

Gets a connector by name.

Parameters:
- `name` (str): Connector name

Returns:
- BaseConnector: Connector instance

## BaseConnector

Base class for all connectors.

### Methods

#### generate_text

```python
async def generate_text(self, prompt: str) -> str
```

Generates text using the AI model.

Parameters:
- `prompt` (str): Input prompt text

Returns:
- str: Generated text

#### summarize_text

```python
async def summarize_text(self, text: str, max_length: int = 500) -> str
```

Creates a summary of the input text.

Parameters:
- `text` (str): Input text to summarize
- `max_length` (int, optional): Maximum length of the summary. Defaults to 500.

Returns:
- str: Summarized text

#### classify_text

```python
async def classify_text(self, text: str, categories: List[str]) -> str
```

Classifies text into predefined categories.

Parameters:
- `text` (str): Text to classify
- `categories` (List[str]): List of possible categories

Returns:
- str: Determined category

#### extract_text_from_image

```python
async def extract_text_from_image(self, image_path: str) -> str
```

Extracts text from an image using OCR.

Parameters:
- `image_path` (str): Path to the image file

Returns:
- str: Extracted text

## ConnectorCapabilities

Enumeration of connector capabilities.

```python
class ConnectorCapabilities(Enum):
    TEXT_GENERATION = "text_generation"
    SUMMARY = "summary"
    CLASSIFICATION = "classification"
    OCR = "ocr"
```

## Constants

```python
API_VERSION = "v1"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
```

## API Endpoints

### Mistral AI

- Base URL: `https://api.mistral.ai/v1`
- Endpoints:
  - Text Generation: `/chat/completions`
  - OCR: `/vision/completions`

### Anthropic

- Base URL: `https://api.anthropic.com/v1`
- Endpoints:
  - Text Generation: `/messages`
  - Summarization: `/summarize`
  - Classification: `/classify` 
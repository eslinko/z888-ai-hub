# BaseConnector - Core Interface for AI Connectors

## 📌 Overview
`BaseConnector` is an abstract class that defines a **standardized interface** for AI connectors.  
Every AI provider (Anthropic, Mistral, OpenAI, etc.) must implement this interface to ensure **consistency and flexibility** in how AI APIs are accessed.

### **✅ Why `BaseConnector`?**
- Standardizes AI API interactions.
- Ensures all connectors follow the same structure.
- Allows easy integration of new AI providers.
- Provides flexibility for different AI tasks (text generation, summarization, OCR, etc.).
- Keeps the core logic clean and modular.

---

## 🛠️ **Class Structure**
The `BaseConnector` serves as a **contract** for all AI connectors.  
Each provider must implement its **own API logic** while conforming to this interface.

### **🔹 Constructor (`__init__`)**
```python
def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None)

"""
JSON document validator.
"""

from typing import Dict, Any
from jsonschema import validate, ValidationError
from .exceptions import JsonValidationError


# Схема документа
DOCUMENT_SCHEMA = {
    "type": "object",
    "required": [
        "file_id",
        "file_name",
        "summary",
        "metadata",
        "paragraphs",
        "created_at",
        "updated_at"
    ],
    "properties": {
        "file_id": {"type": "string"},
        "file_name": {"type": "string"},
        "summary": {"type": "string"},
        "metadata": {
            "type": "object",
            "required": ["size", "original_path"],
            "properties": {
                "size": {"type": "number"},
                "page_count": {"type": ["number", "null"]},
                "language": {"type": "string"},
                "original_path": {"type": "string"}
            }
        },
        "paragraphs": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["paragraph_id", "text"],
                "properties": {
                    "paragraph_id": {"type": "string"},
                    "page_number": {"type": ["number", "null"]},
                    "text": {"type": "string"}
                }
            }
        },
        "created_at": {"type": "string"},
        "updated_at": {"type": "string"}
    }
}


def validate_document(document: Dict[str, Any]) -> None:
    """
    Validate document structure against schema.
    
    Args:
        document: Document data to validate
        
    Raises:
        JsonValidationError: If validation fails
    """
    try:
        validate(instance=document, schema=DOCUMENT_SCHEMA)
    except ValidationError as e:
        raise JsonValidationError(f"Document validation failed: {str(e)}") 
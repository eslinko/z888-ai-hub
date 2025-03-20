"""
Exceptions for document processors.
"""

class ProcessingError(Exception):
    """Base exception for all processing errors."""
    pass


class ContentExtractionError(ProcessingError):
    """Error during content extraction."""
    pass


class MetadataExtractionError(ProcessingError):
    """Error during metadata extraction."""
    pass


class TableExtractionError(ProcessingError):
    """Error during table extraction."""
    pass


class ImageExtractionError(ProcessingError):
    """Error during image extraction."""
    pass


class StyleExtractionError(ProcessingError):
    """Error during style extraction."""
    pass


class ValidationError(ProcessingError):
    """Error during document validation."""
    pass 
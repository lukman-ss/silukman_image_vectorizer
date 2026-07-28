class VectorizationError(Exception):
    """Base exception for all vectorization pipeline errors."""
    pass


class InvalidInputError(VectorizationError):
    """Raised when input file is missing, unsupported, or invalid."""
    pass


class ProcessingError(VectorizationError):
    """Raised when an error occurs during image preprocessing or vectorization."""
    pass


class ExportError(VectorizationError):
    """Raised when an error occurs while writing the output SVG."""
    pass

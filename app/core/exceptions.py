class SilukmanError(Exception):
    """Base exception for all Silukman Image Vectorizer errors."""
    pass


class ConfigurationError(SilukmanError):
    """Raised when there is an error in configuration or preset loading."""
    pass


class InputImageError(SilukmanError):
    """Raised when input file is missing, unsupported, or invalid."""
    pass


class PreprocessingError(SilukmanError):
    """Raised when an error occurs during image preprocessing."""
    pass


class VectorizationError(SilukmanError):
    """Raised when an error occurs during vectorization engine execution."""
    pass


class SvgValidationError(SilukmanError):
    """Raised when an error occurs while parsing or validating the output SVG."""
    pass


class MetricError(SilukmanError):
    """Raised when an error occurs during metric calculation (SSIM, RMSE, etc)."""
    pass


class DatasetError(SilukmanError):
    """Raised when there is an error in the benchmark dataset manifest."""
    pass


class BackendUnavailableError(SilukmanError):
    """Raised when a requested vectorization backend is not installed or available."""
    pass


class ExperimentError(SilukmanError):
    """Raised when there is an error in the benchmark experiment runner."""
    pass


# Keep legacy aliases for backward compatibility if needed, or remove them.
InvalidInputError = InputImageError
ProcessingError = PreprocessingError
ExportError = VectorizationError

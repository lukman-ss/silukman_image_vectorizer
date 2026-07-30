class SilukmanError(Exception):
    """Base exception for all Silukman Image Vectorizer errors."""


class ConfigurationError(SilukmanError):
    """Raised when there is an error in configuration or preset loading."""


class InputImageError(SilukmanError):
    """Raised when input file is missing, unsupported, or invalid."""


class PreprocessingError(SilukmanError):
    """Raised when an error occurs during image preprocessing."""


class VectorizationError(SilukmanError):
    """Raised when an error occurs during vectorization engine execution."""


class SvgValidationError(SilukmanError):
    """Raised when an error occurs while parsing or validating the output SVG."""


class MetricError(SilukmanError):
    """Raised when an error occurs during metric calculation (SSIM, RMSE, etc)."""


class DatasetError(SilukmanError):
    """Raised when there is an error in the benchmark dataset manifest."""


class BackendUnavailableError(SilukmanError):
    """Raised when a requested vectorization backend is not installed or available."""


class ExperimentError(SilukmanError):
    """Raised when there is an error in the benchmark experiment runner."""


# Keep legacy aliases for backward compatibility if needed, or remove them.
InvalidInputError = InputImageError
ProcessingError = PreprocessingError
ExportError = VectorizationError

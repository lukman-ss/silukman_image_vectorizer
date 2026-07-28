from abc import ABC, abstractmethod
from typing import Dict, Any


class VectorizerBackend(ABC):
    """
    Uniform interface for all baseline vectorizers.
    Ensures the benchmark runner does not depend on the implementation details
    of each specific tool.
    """
    
    @abstractmethod
    def name(self) -> str:
        """Returns the canonical name of the backend (e.g. 'Potrace', 'Silukman')."""
        pass
        
    @abstractmethod
    def version(self) -> str:
        """Returns the version of the underlying tool."""
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        """Checks if the tool is installed and available in the current environment."""
        pass
        
    @abstractmethod
    def vectorize(self, input_path: str, output_path: str, preset_name: str, category: str = None) -> Dict[str, Any]:
        """
        Executes the vectorization process.
        
        Args:
            input_path: Path to the input raster image.
            output_path: Path where the SVG should be saved.
            preset_name: The Silukman preset to map parameters from.
            category: The dataset category (for skipping unfair comparisons).
            
        Returns:
            A dictionary containing metadata, performance data, and any errors.
        """
        pass

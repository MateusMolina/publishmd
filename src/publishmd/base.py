"""Base classes for emitters, transformers, and filters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Set


class Emitter(ABC):
    """Base class for all emitters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the emitter with configuration."""
        self.config = config

    @abstractmethod
    def emit(self, files_to_process: List[Path], output_dir: Path) -> List[Path]:
        """
        Emit files to output directory.

        Args:
            files_to_process: List of files to process and emit
            output_dir: Target directory for emitted files

        Returns:
            List of paths to emitted files
        """
        pass


class Transformer(ABC):
    """Base class for all transformers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the transformer with configuration."""
        self.config = config

    @abstractmethod
    def transform(self, file_path: Path, emitted_files: List[Path]) -> None:
        """
        Transform a file in place.

        Args:
            file_path: Path to the file to transform
            emitted_files: List of all emitted files for reference
        """
        pass


class Filter(ABC):
    """Base class for all filters."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the filter with configuration."""
        self.config = config

    @abstractmethod
    def should_include(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on filter criteria.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be included, False otherwise
        """
        pass

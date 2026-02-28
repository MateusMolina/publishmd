"""Base classes for transformers and filters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Set


def read_text_safe(path: Path) -> str:
    """Read a file as text, falling back to latin-1 if it is not valid UTF-8.

    Raises IOError for binary files (detected by the presence of null bytes),
    so callers that wrap this in ``except IOError`` will safely skip them.
    """
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise IOError(f"Binary file skipped: {path}")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


class Transformer(ABC):
    """Base class for all transformers."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the transformer with configuration."""
        self.config = config

    @abstractmethod
    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """
        Transform a file in place.

        Args:
            file_path: Path to the file to transform
            copied_files: Mutable list of all copied output files for reference.
                          Transformers that rename files (e.g. change extension)
                          should update this list in-place.
        """
        pass


class Filter(ABC):
    """Base class for all filters.

    The single abstract method is :meth:`filter`, which receives the **full
    list** of candidate files and returns the subset that should be kept.
    This bulk API lets filters that need cross-file context (e.g.
    ``ReferencedAssetsFilter``) work correctly while still allowing simple
    per-file filters to implement a lightweight ``should_include`` helper
    and delegate to it from ``filter``.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the filter with configuration."""
        self.config = config

    @abstractmethod
    def filter(self, files: List[Path]) -> List[Path]:
        """Return the subset of *files* that should be kept.

        Args:
            files: All candidate files (already collected from the input
                   directory, or the result of a previous filter stage).

        Returns:
            The files that pass this filter.
        """
        pass

"""Base classes for transformers and filters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Set


class FilterSanityError(RuntimeError):
    """Raised when a filter's post-run sanity check detects a violation.

    A sanity check re-applies the filter to the actual output files after the
    full pipeline has finished.  Any file that would have been dropped is
    reported as a violation, indicating that the pipeline incorrectly let a
    file through (e.g. a private document that should have been excluded by the
    frontmatter filter).
    """

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
        self._sanity_check_enabled: bool = bool(config.get("sanity_check", False))
        # Strip the meta-key so subclasses only see their own filter criteria.
        self.config = {k: v for k, v in config.items() if k != "sanity_check"}

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

    def sanity_check(self, output_files: List[Path]) -> None:
        """Verify that every file in *output_files* would still pass this filter.

        Re-applies :meth:`filter` to the actual output files after the full
        pipeline has finished.  Any file that would be dropped is reported as
        a violation and :class:`FilterSanityError` is raised.

        The check is only performed when ``sanity_check: true`` is set in the
        filter's config block.  Subclasses may override this method for more
        specialised checks.

        Args:
            output_files: Final list of output files (after all transformers).

        Raises:
            FilterSanityError: If any output file would be rejected by this filter.
        """
        if not self._sanity_check_enabled:
            return

        kept = set(self.filter(output_files))
        violations = [f for f in output_files if f not in kept]
        if violations:
            names = ", ".join(str(v) for v in violations)
            raise FilterSanityError(
                f"{self.__class__.__name__} sanity check failed — "
                f"{len(violations)} file(s) in the output should have been excluded:\n"
                f"  {names}"
            )

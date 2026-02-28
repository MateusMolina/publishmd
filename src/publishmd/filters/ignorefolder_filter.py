"""Ignore-folder filter - excludes files residing inside specified folders."""

from pathlib import Path
from typing import Any, Dict, List

from ..base import Filter


class IgnoreFolderFilter(Filter):
    """Filter that excludes any file whose path contains one of the ignored folders.

    Configuration example (config.yaml)::

        filters:
          - name: ignorefolder_filter
            type: publishmd.filters.ignorefolder_filter.IgnoreFolderFilter
            config:
              ignored_folders:
                - drafts
                - private
                - _archive
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the filter.

        Args:
            config: Configuration dictionary supporting:
                - ignored_folders: list of folder names/paths to ignore (default [])
        """
        super().__init__(config)
        raw: List[str] = config.get("ignored_folders", [])
        # Normalise each entry as a pure-path so comparisons work cross-platform
        self.ignored_folders: List[Path] = [Path(f) for f in raw]

    def filter(self, files: List[Path]) -> List[Path]:
        """Return *files* with any path inside an ignored folder removed."""
        if not self.ignored_folders:
            return list(files)
        return [f for f in files if not self._is_inside_ignored(f)]

    def _is_inside_ignored(self, file_path: Path) -> bool:
        """Return True when *file_path* lives inside any of the ignored folders."""
        resolved = file_path.resolve()
        for ignored in self.ignored_folders:
            ignored_parts = ignored.parts
            for parent in [resolved, *resolved.parents]:
                candidate_parts = parent.parts
                if len(candidate_parts) >= len(ignored_parts):
                    tail = candidate_parts[-len(ignored_parts):]
                    if tail == ignored_parts:
                        return True
        return False

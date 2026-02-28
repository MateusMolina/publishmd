"""Folder filter - keeps only files that reside inside specified folders (allowlist)."""

from pathlib import Path
from typing import Any, Dict, List

from ..base import Filter


class FolderFilter(Filter):
    """Keep only files whose path is inside one of the configured folders.

    This is the allowlist counterpart of :class:`IgnoreFolderFilter`.  Where
    that filter *blocks* listed folders, this filter *only allows* files that
    live inside one of the listed folders.

    Configuration example (config.yaml)::

        filters:
          - name: folder_filter
            type: publishmd.filters.folder_filter.FolderFilter
            config:
              included_folders:
                - posts
                - pages
                - content/published
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialise the filter.

        Args:
            config: Dictionary supporting:
                - included_folders: list of folder names/relative paths that a
                  file must reside inside to be kept (default []).  When the
                  list is empty every file is kept (no-op behaviour).
        """
        super().__init__(config)
        raw: List[str] = config.get("included_folders", [])
        self.included_folders: List[Path] = [Path(f) for f in raw]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, files: List[Path]) -> List[Path]:
        """Return only the files that reside inside an included folder."""
        if not self.included_folders:
            return list(files)
        return [f for f in files if self._is_inside_included(f)]

    def _is_inside_included(self, file_path: Path) -> bool:
        """Return True when *file_path* lives inside any of the included folders."""
        resolved = file_path.resolve()
        for included in self.included_folders:
            included_parts = included.parts
            for parent in [resolved, *resolved.parents]:
                candidate_parts = parent.parts
                if len(candidate_parts) >= len(included_parts):
                    tail = candidate_parts[-len(included_parts):]
                    if tail == included_parts:
                        return True
        return False

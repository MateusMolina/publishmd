"""Folder filter - keeps only files that reside inside specified folders (allowlist)."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Filter


class FolderFilter(Filter):
    """Keep only files whose path is inside one of the configured folders.

    This is the allowlist counterpart of :class:`IgnoreFolderFilter`.  Where
    that filter *blocks* listed folders, this filter *only allows* files that
    live inside one of the listed folders.

    The special option ``include_root: true`` additionally keeps files that sit
    directly in the root of the input tree (i.e. not inside any sub-folder).
    The root is inferred automatically as the deepest common ancestor of all
    files passed to :meth:`filter`.

    Configuration examples (config.yaml)::

        # Keep only files inside posts/ or pages/ (no root files)
        filters:
          - name: folder_filter
            type: publishmd.filters.folder_filter.FolderFilter
            config:
              included_folders:
                - posts
                - pages

        # Keep posts/ AND root-level files (e.g. index.md next to posts/)
        filters:
          - name: folder_filter
            type: publishmd.filters.folder_filter.FolderFilter
            config:
              include_root: true
              included_folders:
                - posts
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialise the filter.

        Args:
            config: Dictionary supporting:
                - included_folders: list of folder names/relative paths that a
                  file must reside inside to be kept (default []).  When the
                  list is empty and ``include_root`` is also false, every file
                  is kept (no-op behaviour).
                - include_root: when ``true``, files that live directly in the
                  root of the input tree are kept regardless of
                  ``included_folders`` (default false).
        """
        super().__init__(config)
        raw: List[str] = self.config.get("included_folders", [])
        self.included_folders: List[Path] = [Path(f) for f in raw]
        self._include_root: bool = bool(self.config.get("include_root", False))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, files: List[Path]) -> List[Path]:
        """Return only the files that reside inside an included folder or at root."""
        if not self.included_folders and not self._include_root:
            return list(files)

        root: Optional[Path] = (
            self._common_parent(files) if self._include_root else None
        )

        result: List[Path] = []
        for f in files:
            if self._include_root and root is not None and f.resolve().parent == root:
                result.append(f)
            elif self._is_inside_included(f):
                result.append(f)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _common_parent(files: List[Path]) -> Optional[Path]:
        """Return the deepest directory that is an ancestor of every path."""
        if not files:
            return None
        resolved = [p.resolve() for p in files]
        common = resolved[0].parent
        for p in resolved[1:]:
            while common not in p.parents and common != p.parent:
                common = common.parent
        return common

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

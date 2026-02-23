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

    def should_include(self, file_path: Path) -> bool:
        """
        Return False if *file_path* lives inside any of the ignored folders.

        Matching is done against each part of the resolved path, so both
        simple folder names (e.g. ``drafts``) and relative sub-paths
        (e.g. ``content/drafts``) are supported.

        Args:
            file_path: Path to the file to evaluate.

        Returns:
            True if the file should be included, False if it should be ignored.
        """
        resolved = file_path.resolve()

        for ignored in self.ignored_folders:
            ignored_parts = ignored.parts  # e.g. ('content', 'drafts')

            # Walk up through the parents of *resolved* and look for a match
            for parent in [resolved, *resolved.parents]:
                # Try matching the tail of *parent* against *ignored*
                candidate_parts = parent.parts
                if len(candidate_parts) >= len(ignored_parts):
                    tail = candidate_parts[-len(ignored_parts):]
                    if tail == ignored_parts:
                        return False

        return True

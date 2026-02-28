"""Extension filter - keeps only files whose extension is in an allow-list."""

from pathlib import Path
from typing import Any, Dict, List

from ..base import Filter


class ExtensionFilter(Filter):
    """Keep only files whose extension is in the configured allow-list.

    Configuration example (config.yaml)::

        filters:
          - name: extension_filter
            type: publishmd.filters.extension_filter.ExtensionFilter
            config:
              extensions:
                - .md
                - .qmd
                - .markdown
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialise the filter.

        Args:
            config: Dictionary supporting:
                - extensions: list of file extensions to keep (with leading dot,
                  e.g. ``[".md", ".qmd"]``).  Case-insensitive comparison is used.
        """
        super().__init__(config)
        raw: List[str] = config.get("extensions", [])
        self.extensions: List[str] = [ext.lower() for ext in raw]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, files: List[Path]) -> List[Path]:
        """Return only the files whose extension is in the allow-list."""
        if not self.extensions:
            return list(files)
        return [f for f in files if f.suffix.lower() in self.extensions]

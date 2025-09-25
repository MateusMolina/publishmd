"""Frontmatter filter - filters files based on YAML frontmatter criteria."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from ..base import Filter


class FrontmatterFilter(Filter):
    """Filter files based on YAML frontmatter criteria."""

    def should_include(self, file_path: Path) -> bool:
        """
        Check if a file should be included based on frontmatter filters.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be included, False otherwise
        """
        # Only process markdown and QMD files with this filter
        if file_path.suffix not in [".md", ".markdown", ".qmd"]:
            return False

        if not self.config:
            return True

        frontmatter = self._extract_frontmatter(file_path)
        if not frontmatter:
            return False

        # Check all filter conditions
        for key, expected_value in self.config.items():
            if key not in frontmatter:
                return False
            if frontmatter[key] != expected_value:
                return False

        return True

    def _extract_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract YAML frontmatter from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary containing frontmatter, or None if no frontmatter found
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for YAML frontmatter
            if not content.startswith("---"):
                return None

            # Find the end of frontmatter
            match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
            if not match:
                return None

            frontmatter_text = match.group(1)

            # Use a custom loader to preserve string values for dates
            class StringPreservingLoader(yaml.SafeLoader):
                pass

            def construct_yaml_object(self, node):
                return self.construct_yaml_str(node)

            # Override date parsing to return strings
            StringPreservingLoader.add_constructor(
                "tag:yaml.org,2002:timestamp", construct_yaml_object
            )

            return yaml.load(frontmatter_text, Loader=StringPreservingLoader)

        except (IOError, yaml.YAMLError):
            return None

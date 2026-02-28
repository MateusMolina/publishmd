"""Frontmatter filter - filters files based on YAML frontmatter criteria."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Filter, read_text_safe


class FrontmatterFilter(Filter):
    """Filter files based on YAML frontmatter criteria.

    Markdown/QMD files are kept only when their frontmatter satisfies every
    key-value pair in the config.  All other file types pass through
    unconditionally — this filter only concerns itself with text files that
    may carry YAML frontmatter.
    """

    def filter(self, files: List[Path]) -> List[Path]:
        """Return the subset of *files* that passes the frontmatter criteria.

        Non-markdown files always pass through.  Markdown files are kept only
        when their frontmatter satisfies every configured key-value pair.
        """
        result: List[Path] = []
        for f in files:
            # Non-markdown passes through unconditionally
            if f.suffix not in [".md", ".markdown", ".qmd"]:
                result.append(f)
                continue
            # No criteria configured → keep all markdown too
            if not self.config:
                result.append(f)
                continue
            frontmatter = self._extract_frontmatter(f)
            if not frontmatter:
                continue
            if all(frontmatter.get(k) == v for k, v in self.config.items()):
                result.append(f)
        return result

    def _extract_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Extract YAML frontmatter from a markdown file.

        Args:
            file_path: Path to the markdown file

        Returns:
            Dictionary containing frontmatter, or None if no frontmatter found
        """
        try:
            content = read_text_safe(file_path)

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

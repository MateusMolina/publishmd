"""Tags to categories transformer - converts frontmatter 'tags' to 'categories'."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Transformer


class TagsToCategoriesTransformer(Transformer):
    """Transformer that converts frontmatter 'tags' field to 'categories'."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the tags to categories transformer."""
        super().__init__(config)
        # No specific config needed for this transformer

    def transform(self, file_path: Path, emitted_files: List[Path]) -> None:
        """
        Transform frontmatter by converting 'tags' to 'categories'.

        Args:
            file_path: Path to the file to transform
            emitted_files: List of all emitted files for reference
        """
        if not file_path.exists():
            return
        
        # Only process Markdown and Quarto Markdown files
        if not file_path.suffix in ['.md', '.qmd']:
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Extract and update frontmatter
            updated_content, modified = self._update_frontmatter(content)

            # Only write if content changed
            if modified and updated_content != original_content:
                file_path.write_text(updated_content, encoding="utf-8")

        except IOError:
            pass

    def _update_frontmatter(self, content: str) -> tuple[str, bool]:
        """
        Update frontmatter by converting tags to categories.

        Args:
            content: The full file content

        Returns:
            Tuple of (updated_content, was_modified)
        """
        # Check for YAML frontmatter
        if not content.startswith("---"):
            return content, False

        # Find the end of frontmatter
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return content, False

        frontmatter_text = match.group(1)
        body = content[match.end():]

        try:
            # Parse frontmatter
            frontmatter = yaml.safe_load(frontmatter_text)
            if not isinstance(frontmatter, dict):
                return content, False

            modified = False

            # Check if tags exist
            if "tags" in frontmatter:
                tags = frontmatter.pop("tags")

                # Ensure tags is a list
                if not isinstance(tags, list):
                    tags = [tags]

                # Check if categories already exists
                if "categories" in frontmatter:
                    existing_categories = frontmatter["categories"]
                    if not isinstance(existing_categories, list):
                        existing_categories = [existing_categories]

                    # Merge tags into categories, avoiding duplicates
                    merged_categories = existing_categories + [tag for tag in tags if tag not in existing_categories]
                    frontmatter["categories"] = merged_categories
                else:
                    frontmatter["categories"] = tags

                modified = True

            if modified:
                # Serialize back to YAML
                updated_frontmatter_text = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
                updated_content = f"---\n{updated_frontmatter_text}---\n{body}"
                return updated_content, True
            else:
                return content, False

        except yaml.YAMLError:
            # If YAML parsing fails, return original content
            return content, False
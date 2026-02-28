"""Rename frontmatter field transformer - renames a frontmatter key to another name."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List

from ..base import Transformer, read_text_safe

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


class RenameFrontmatterFieldTransformer(Transformer):
    """Transformer that renames a single frontmatter field.

    Config keys:
        from_field (str): The existing frontmatter key to rename.
        to_field   (str): The target key name to use instead.
        overwrite  (bool, optional): When True, overwrite *to_field* if it
                   already exists in the frontmatter. Defaults to False (skip).

    Multiple instances of this transformer can be added to a pipeline config,
    each handling a different rename, e.g.::

        - name: rename_modified
          type: publishmd.transformers.rename_frontmatter_field_transformer.RenameFrontmatterFieldTransformer
          config:
            from_field: modified
            to_field: date-modified

        - name: rename_created
          type: publishmd.transformers.rename_frontmatter_field_transformer.RenameFrontmatterFieldTransformer
          config:
            from_field: created
            to_field: date
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.from_field: str = config["from_field"]
        self.to_field: str = config["to_field"]
        self.overwrite: bool = config.get("overwrite", False)

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """Rename *from_field* to *to_field* in the frontmatter of *file_path*."""
        if not file_path.exists():
            return

        try:
            content = read_text_safe(file_path)
            updated, modified = self._rename_field(content)
            if modified:
                file_path.write_text(updated, encoding="utf-8")
        except IOError:
            pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rename_field(self, content: str) -> tuple[str, bool]:
        """Return *(updated_content, was_modified)*.

        Parses the YAML frontmatter block, renames the key, and serialises it
        back.  The rest of the file body is left untouched.
        """
        if not content.startswith("---"):
            return content, False

        match = _FRONTMATTER_RE.match(content)
        if not match:
            return content, False

        frontmatter_text = match.group(1)
        body = content[match.end():]

        try:
            frontmatter = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError:
            return content, False

        if not isinstance(frontmatter, dict):
            return content, False

        if self.from_field not in frontmatter:
            return content, False

        # Skip if target already exists and overwrite is disabled
        if self.to_field in frontmatter and not self.overwrite:
            return content, False

        value = frontmatter.pop(self.from_field)
        frontmatter[self.to_field] = value

        updated_fm = yaml.dump(
            frontmatter, default_flow_style=False, allow_unicode=True
        )
        return f"---\n{updated_fm}---\n{body}", True

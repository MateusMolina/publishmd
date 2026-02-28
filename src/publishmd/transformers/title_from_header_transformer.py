"""Title from header transformer - syncs frontmatter title with first H1 header."""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..base import Transformer, read_text_safe


class _QuotedStr(str):
    """A str subclass that yaml will always serialize with double quotes."""


def _make_dumper() -> type:
    """Return a yaml Dumper that renders _QuotedStr values with double quotes."""

    class _QuotedDumper(yaml.Dumper):  # type: ignore[misc]
        pass

    def _represent_quoted(dumper: yaml.Dumper, value: str) -> yaml.ScalarNode:
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style='"')

    _QuotedDumper.add_representer(_QuotedStr, _represent_quoted)
    return _QuotedDumper


class TitleFromHeaderTransformer(Transformer):
    """Transformer that syncs the frontmatter ``title`` field with the first H1 header.

    Behaviour:

    * **Front matter has ``title``** — the first ``# …`` header is removed so
      the title is not duplicated in the rendered output.
    * **Front matter has no ``title``** — the text of the first ``# …`` header
      is promoted to ``title:`` in the frontmatter and the header is removed.
    * **No H1 found** — the file is left unchanged.

    This transformer takes no configuration keys::

        - name: title_from_header
          type: publishmd.transformers.title_from_header_transformer.TitleFromHeaderTransformer
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the title from header transformer."""
        super().__init__(config)

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """
        Transform the file by syncing frontmatter title with the first H1 header.

        Args:
            file_path: Path to the file to transform
            copied_files: List of all copied files for reference
        """
        if not file_path.exists():
            return

        try:
            content = read_text_safe(file_path)
            updated_content, modified = self._process(content)

            if modified and updated_content != content:
                file_path.write_text(updated_content, encoding="utf-8")

        except IOError:
            pass

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process(self, content: str) -> Tuple[str, bool]:
        """Apply the transformation logic to raw file content.

        Returns:
            Tuple of (updated_content, was_modified)
        """
        frontmatter, body = self._split_frontmatter(content)

        # Find the first H1 header in the body
        header_title, body_without_header = self._extract_first_h1(body)

        if header_title is None:
            # No H1 found – nothing to do
            return content, False

        if frontmatter is None:
            # No frontmatter at all – create one with the title
            new_frontmatter_text = yaml.dump(
                {"title": _QuotedStr(header_title)},
                Dumper=_make_dumper(),
                default_flow_style=False,
                allow_unicode=True,
            )
            updated_content = f"---\n{new_frontmatter_text}---\n{body_without_header}"
            return updated_content, True

        try:
            parsed = yaml.safe_load(frontmatter)
        except yaml.YAMLError:
            return content, False

        if not isinstance(parsed, dict):
            parsed = {}

        if "title" not in parsed:
            # Add title from H1 header
            parsed["title"] = _QuotedStr(header_title)
        elif isinstance(parsed["title"], str):
            parsed["title"] = _QuotedStr(parsed["title"])

        # In both branches we remove the H1 header from the body
        updated_frontmatter_text = yaml.dump(
            parsed, Dumper=_make_dumper(), default_flow_style=False, allow_unicode=True
        )
        updated_content = f"---\n{updated_frontmatter_text}---\n{body_without_header}"
        return updated_content, True

    @staticmethod
    def _split_frontmatter(content: str) -> Tuple[Optional[str], str]:
        """Split content into (frontmatter_text, body).

        Returns (None, content) when no YAML frontmatter block is present.
        """
        if not content.startswith("---"):
            return None, content

        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return None, content

        frontmatter_text = match.group(1)
        body = content[match.end():]
        return frontmatter_text, body

    @staticmethod
    def _extract_first_h1(body: str) -> Tuple[Optional[str], str]:
        """Find and remove the first H1 header from the body text.

        Returns:
            Tuple of (header_title, body_without_h1).
            header_title is None when no H1 is found.
        """
        # Match a line that starts with a single '#' (not '##' etc.)
        pattern = re.compile(r"^# (.+)\n?", re.MULTILINE)
        match = pattern.search(body)
        if not match:
            return None, body

        header_title = match.group(1).strip()

        # Remove the header line; collapse any resulting doubled blank lines
        body_without_header = body[: match.start()] + body[match.end():]

        # Strip a single leading newline that is commonly left behind
        if body_without_header.startswith("\n"):
            body_without_header = body_without_header[1:]

        return header_title, body_without_header

"""Code fence transformer - rewrites bare code fences to Quarto-style fences."""

import re
from pathlib import Path
from typing import Any, Dict, List

from ..base import Transformer, read_text_safe

_TEXT_EXTENSIONS = {".md", ".qmd", ".txt", ".html", ".htm", ".markdown"}

_DEFAULT_LANGUAGES = ["mermaid", "plantuml"]


class CodeFenceTransformer(Transformer):
    """Transformer that converts bare language-tagged code fences to
    Quarto-style brace-wrapped fences.

    For example::

        ```mermaid          →   ```{mermaid}
        graph LR               graph LR
        A --> B                A --> B
        ```                    ```

    Config keys:
        languages (list[str]): Language identifiers to convert.
                               Defaults to ``["mermaid", "plantuml"]``.

    Example YAML::

        - name: quarto_fences
          type: publishmd.transformers.code_fence_transformer.CodeFenceTransformer
          config:
            languages:
              - mermaid
              - plantuml
              - dot
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.languages: List[str] = list(
            config.get("languages", _DEFAULT_LANGUAGES)
        )

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """Rewrite code fences in *file_path*.

        Args:
            file_path: Path to the file currently being transformed.
            copied_files: Unused; present for interface compatibility.
        """
        if not file_path.exists():
            return

        if file_path.suffix.lower() not in _TEXT_EXTENSIONS:
            return

        try:
            content = read_text_safe(file_path)
        except IOError:
            return

        original = content

        for lang in self.languages:
            # Match ``` (optional spaces) <lang> (optional trailing spaces)
            # only when NOT already wrapped in braces.
            pattern = re.compile(
                r"^([ \t]*```+[ \t]*)" + re.escape(lang) + r"([ \t]*)$",
                re.MULTILINE,
            )
            replacement = r"\g<1>{" + lang + r"}\g<2>"
            content = pattern.sub(replacement, content)

        if content != original:
            file_path.write_text(content, encoding="utf-8")

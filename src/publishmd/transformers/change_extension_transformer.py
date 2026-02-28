"""Change extension transformer - renames copied files to a different extension."""

import re
from pathlib import Path
from typing import Any, Dict, List

from ..base import Transformer, read_text_safe

_TEXT_EXTENSIONS = {".md", ".qmd", ".txt", ".html", ".htm", ".markdown"}


class ChangeExtensionTransformer(Transformer):
    """Transformer that renames output files from one extension to another and
    updates all cross-file links accordingly.

    This transformer is stateful: on its **first** call it

    1. Scans *copied_files* for any file whose suffix matches one of the
       configured ``from_extensions``.
    2. Renames those files on disk (``file.md`` → ``file.qmd``).
    3. Updates *copied_files* in-place so that subsequent transformers see the
       new paths.
    4. Builds an internal rename map used for link rewriting.

    On **every** call it rewrites links inside *file_path* to point to the
    renamed paths.

    Config keys:
        from_extensions (list[str]): Extensions to rename, e.g. ``[".md", ".markdown"]``.
                                     Defaults to ``[".md", ".markdown"]``.
        to_extension    (str):       Target extension, e.g. ``".qmd"``.
                                     Defaults to ``".qmd"``.

    Example YAML::

        - name: md_to_qmd
          type: publishmd.transformers.change_extension_transformer.ChangeExtensionTransformer
          config:
            from_extensions:
              - ".md"
              - ".markdown"
            to_extension: ".qmd"
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        raw_from = config.get("from_extensions", [".md", ".markdown"])
        self.from_extensions: List[str] = [
            ext if ext.startswith(".") else f".{ext}" for ext in raw_from
        ]
        to_ext = config.get("to_extension", ".qmd")
        self.to_extension: str = to_ext if to_ext.startswith(".") else f".{to_ext}"

        # Maps old stem-based filename variants → new filename (for link rewriting)
        self._rename_map: Dict[str, str] = {}
        self._initialized: bool = False

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """Rename matching files (first call) and update links in *file_path*.

        Args:
            file_path: Path to the file currently being transformed.
            copied_files: Mutable list of all copied output files; updated
                          in-place when files are renamed.
        """
        if not self._initialized:
            self._apply_renames(copied_files)
            self._initialized = True

        if not file_path.exists():
            return

        if file_path.suffix.lower() not in _TEXT_EXTENSIONS:
            return

        self._update_links(file_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_renames(self, copied_files: List[Path]) -> None:
        """Rename all matching files on disk, build the rename map, and update
        links inside the renamed files immediately afterwards."""
        renamed_new_paths: List[Path] = []

        for i, path in enumerate(copied_files):
            if path.suffix.lower() not in self.from_extensions:
                continue

            new_path = path.with_suffix(self.to_extension)
            if new_path == path:
                continue

            path.rename(new_path)

            # Record both the plain and the common URL-encoded (%20) variants
            old_name = path.name
            new_name = new_path.name
            self._rename_map[old_name] = new_name
            self._rename_map[old_name.replace(" ", "%20")] = new_name.replace(
                " ", "%20"
            )

            copied_files[i] = new_path
            renamed_new_paths.append(new_path)

        # Now that the full rename map is built, update links in every renamed file
        for new_path in renamed_new_paths:
            if new_path.suffix.lower() in _TEXT_EXTENSIONS:
                self._update_links(new_path)

    def _update_links(self, file_path: Path) -> None:
        """Rewrite links in *file_path* that point to any renamed file."""
        if not self._rename_map:
            return

        try:
            content = read_text_safe(file_path)
        except IOError:
            return

        original = content

        # Match markdown links [text](target) and images ![text](target)
        link_pattern = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")

        def _replace(m: re.Match) -> str:
            prefix = m.group(1)
            target = m.group(2)

            # Only the filename portion matters; keep any fragment/query intact
            fragment = ""
            if "#" in target:
                target, fragment = target.split("#", 1)
                fragment = "#" + fragment
            query = ""
            if "?" in target:
                target, query = target.split("?", 1)
                query = "?" + query

            filename = Path(target).name
            if filename in self._rename_map:
                new_name = self._rename_map[filename]
                new_target = str(Path(target).with_name(new_name))
                return f"{prefix}({new_target}{query}{fragment})"

            return m.group(0)

        content = link_pattern.sub(_replace, content)

        if content != original:
            file_path.write_text(content, encoding="utf-8")

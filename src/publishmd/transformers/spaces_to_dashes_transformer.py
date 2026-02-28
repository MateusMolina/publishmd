"""Spaces to dashes transformer - renames files with spaces to use dashes and updates links."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote, unquote

from ..base import Transformer, read_text_safe

_TEXT_EXTENSIONS = {".md", ".qmd", ".txt", ".html", ".htm"}


class SpacesToDashesTransformer(Transformer):
    """Transformer that renames copied files with spaces in their names to use
    dashes instead, and updates all markdown links across all files accordingly.

    This transformer is stateful: on its first call it pre-computes every needed
    rename, applies them on disk, and mutates *copied_files* in-place so that
    subsequent transformers see the updated paths.  Subsequent calls only update
    links in the supplied file.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the spaces-to-dashes transformer."""
        super().__init__(config)
        # Maps old filename (plain and URL-encoded) → new filename (no spaces)
        self._rename_map: Dict[str, str] = {}
        self._initialized: bool = False

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """
        Rename files with spaces and update links in *file_path*.

        On the very first invocation the transformer scans *copied_files* for
        any paths whose filename contains spaces, renames those files on disk,
        and records the mapping.  Every invocation then rewrites links inside
        *file_path* to reference the new (dash-separated) filenames.

        Args:
            file_path: Path to the file currently being transformed.
            copied_files: Mutable list of all emitted output files; updated
                           in-place when files are renamed.
        """
        if not self._initialized:
            renamed_paths = self._precompute_renames(copied_files)
            self._initialized = True
            # Files that were renamed will not be visited again by the processor
            # (it holds a snapshot of the old paths and skips missing ones).
            # Update links inside each renamed file right here, now that the
            # full rename map is built.
            for new_path in renamed_paths:
                if new_path.suffix.lower() in _TEXT_EXTENSIONS:
                    self._update_links(new_path)

        # The file itself may have been renamed by _precompute_renames;
        # resolve file_path to its new name so we don't double-skip it.
        if not file_path.exists() and file_path.name in self._rename_map:
            file_path = file_path.parent / self._rename_map[file_path.name]

        if not file_path.exists():
            return

        # Only rewrite content in recognisable text files
        if file_path.suffix.lower() not in _TEXT_EXTENSIONS:
            return

        self._update_links(file_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _precompute_renames(self, copied_files: List[Path]) -> List[Path]:
        """Rename every file in *copied_files* whose name contains spaces.

        Updates *copied_files* in-place so the processor loop (and later
        transformers) work with the corrected paths.

        Returns:
            List of new (post-rename) paths for every file that was renamed.
        """
        renamed_new_paths: List[Path] = []
        for i, file_path in enumerate(copied_files):
            if " " not in file_path.name:
                continue

            new_name = file_path.name.replace(" ", "-")
            new_path = file_path.parent / new_name

            if file_path.exists():
                file_path.rename(new_path)

            # Record both the plain-text and URL-encoded form of the old name
            # so we can match either variant inside markdown links.
            self._rename_map[file_path.name] = new_name
            encoded_old = quote(file_path.name, safe="")
            if encoded_old != file_path.name:
                self._rename_map[encoded_old] = new_name

            # Propagate the rename back into the shared copied_files list
            copied_files[i] = new_path
            renamed_new_paths.append(new_path)

        return renamed_new_paths

    def _update_links(self, file_path: Path) -> None:
        """Rewrite markdown/HTML links in *file_path* that point to renamed files.

        Handles:
        * standard markdown links  ``[text](target)``
        * image markdown links     ``![alt](target)``
        * HTML src/href attributes ``src="target"`` / ``href="target"``
        """
        if not self._rename_map or not file_path.exists():
            return

        try:
            content = read_text_safe(file_path)
            original_content = content

            # ---- markdown / image links: ](target) ----
            def _replace_md_target(match: re.Match) -> str:
                target = match.group(1)
                new_target = self._apply_renames(target)
                if new_target != target:
                    return f"]({new_target})"
                return match.group(0)

            content = re.sub(r"\]\(([^)]+)\)", _replace_md_target, content)

            # ---- HTML src="..." / href="..." ----
            def _replace_html_attr(match: re.Match) -> str:
                attr = match.group(1)   # 'src' or 'href'
                quote_char = match.group(2)  # '"' or "'"
                target = match.group(3)
                new_target = self._apply_renames(target)
                if new_target != target:
                    return f'{attr}={quote_char}{new_target}{quote_char}'
                return match.group(0)

            content = re.sub(
                r'(src|href)=(["\'])([^"\']+)\2',
                _replace_html_attr,
                content,
            )

            if content != original_content:
                file_path.write_text(content, encoding="utf-8")

        except IOError:
            pass

    def _apply_renames(self, target: str) -> str:
        """Replace any old filename occurrences in *target* with new names.

        Iterates over accumulated rename entries so that a single target such as
        ``./fourth%20page.qmd`` gets its space-bearing filename replaced with
        ``fourth-page.qmd`` → ``./fourth-page.qmd``.
        """
        result = target
        for old_name, new_name in self._rename_map.items():
            # Only replace when `old_name` appears as a path component, i.e.
            # preceded by '/', './' or at the start of the target string.
            # This avoids accidentally replacing substring matches inside other
            # longer filenames.
            if old_name in result:
                result = result.replace(old_name, new_name)
        return result

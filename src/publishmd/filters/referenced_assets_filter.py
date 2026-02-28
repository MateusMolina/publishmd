"""Referenced-assets filter - keeps only asset files that are referenced by text files."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..base import Filter

# Patterns that may contain asset paths inside text/markdown files
_RE_MARKDOWN_IMAGE = re.compile(r"!\[.*?\]\((.+?)\)")
_RE_MARKDOWN_LINK = re.compile(r"\[.*?\]\((.+?)\)")
_RE_HTML_IMG = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_RE_WIKILINK_IMAGE = re.compile(r"!\[\[(.+?)(?:\|.*?)?\]\]")


class ReferencedAssetsFilter(Filter):
    """Keep text files and only those asset files actually referenced by a text file.

    Unreferenced assets (images, PDFs, videos, …) are dropped from the output
    list.  This mirrors the old ``AssetsEmitter`` behaviour where only
    *referenced* assets were copied to the output directory.

    Configuration example (config.yaml)::

        filters:
          - name: referenced_assets_filter
            type: publishmd.filters.referenced_assets_filter.ReferencedAssetsFilter
            config:
              text_extensions:
                - .md
                - .qmd
                - .markdown
              asset_extensions:
                - .png
                - .jpg
                - .jpeg
                - .gif
                - .svg
                - .pdf
                - .mp4
                - .mov
                - .webp
                - .bib
    """

    _DEFAULT_TEXT_EXTS = {".md", ".markdown", ".qmd", ".html", ".htm", ".txt"}
    _DEFAULT_ASSET_EXTS = {
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf",
        ".mp4", ".mov", ".webm", ".webp", ".ico", ".bib",
        ".eps", ".tiff", ".tif",
    }

    def __init__(self, config: Dict[str, Any]):
        """Initialise the filter.

        Args:
            config: Dictionary supporting:
                - text_extensions: extensions of files that are scanned for
                  asset references (default: a common set of text formats).
                - asset_extensions: extensions treated as assets; only
                  referenced ones are kept (default: common image/media/bib).
        """
        super().__init__(config)
        raw_text = config.get("text_extensions", None)
        raw_asset = config.get("asset_extensions", None)

        self.text_extensions: Set[str] = (
            {e.lower() for e in raw_text} if raw_text else set(self._DEFAULT_TEXT_EXTS)
        )
        self.asset_extensions: Set[str] = (
            {e.lower() for e in raw_asset} if raw_asset else set(self._DEFAULT_ASSET_EXTS)
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def filter(self, files: List[Path]) -> List[Path]:
        """Return text files + all asset files that are referenced by them.

        Files whose extension belongs to neither category are passed through
        unchanged.
        """
        text_files: List[Path] = []
        asset_files: List[Path] = []
        other_files: List[Path] = []

        for f in files:
            ext = f.suffix.lower()
            if ext in self.text_extensions:
                text_files.append(f)
            elif ext in self.asset_extensions:
                asset_files.append(f)
            else:
                other_files.append(f)

        if not asset_files:
            # Nothing to filter; short-circuit
            return files

        asset_set: Set[Path] = set(asset_files)
        root: Optional[Path] = self._find_common_parent(files)

        referenced: Set[Path] = set()
        for tf in text_files:
            referenced.update(self._extract_referenced_assets(tf, root, asset_set))

        kept_assets = sorted(a for a in asset_files if a in referenced)
        return text_files + other_files + kept_assets

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_common_parent(file_paths: List[Path]) -> Optional[Path]:
        """Return the deepest directory that is a parent of every path."""
        if not file_paths:
            return None
        resolved = [p.resolve() for p in file_paths]
        common = resolved[0].parent
        for p in resolved[1:]:
            # Walk up until common is a prefix of p
            while common not in p.parents and common != p.parent:
                common = common.parent
        return common

    @staticmethod
    def _is_url(path_str: str) -> bool:
        """Return True for http/https/ftp/mailto and other non-file URIs."""
        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://", path_str))

    def _is_asset_path(self, path_str: str) -> bool:
        """Return True when *path_str*'s extension looks like an asset."""
        return Path(path_str).suffix.lower() in self.asset_extensions

    def _resolve_path(
        self,
        path_str: str,
        source_file: Path,
        root: Optional[Path],
        asset_set: Set[Path],
    ) -> Optional[Path]:
        """Try to resolve *path_str* to one of the known asset paths.

        Resolution order:
        1. Relative to the directory of *source_file*.
        2. Relative to *root* (project root, i.e. common parent of all files).
        3. Basename-only search inside *asset_set* (for bare wikilink names).
        """
        if self._is_url(path_str):
            return None

        # Strip any leading #fragment
        path_str = path_str.split("#")[0].strip()
        if not path_str:
            return None

        p = Path(path_str)

        # 1. relative to the source file's directory
        candidate = (source_file.parent / p).resolve()
        if candidate in asset_set:
            return candidate

        # 2. relative to project root
        if root is not None:
            candidate = (root / p).resolve()
            if candidate in asset_set:
                return candidate

        # 3. bare filename — search asset_set for a matching name
        name = p.name
        for ap in asset_set:
            if ap.name == name:
                return ap

        return None

    def _extract_referenced_assets(
        self,
        file_path: Path,
        root: Optional[Path],
        asset_set: Set[Path],
    ) -> Set[Path]:
        """Scan *file_path* and return every asset from *asset_set* it references."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return set()

        found: Set[Path] = set()

        def _check(path_str: str) -> None:
            if not path_str or self._is_url(path_str):
                return
            if not self._is_asset_path(path_str):
                return
            resolved = self._resolve_path(path_str, file_path, root, asset_set)
            if resolved is not None:
                found.add(resolved)

        for m in _RE_MARKDOWN_IMAGE.finditer(content):
            _check(m.group(1).strip())

        for m in _RE_MARKDOWN_LINK.finditer(content):
            _check(m.group(1).strip())

        for m in _RE_HTML_IMG.finditer(content):
            _check(m.group(1).strip())

        for m in _RE_WIKILINK_IMAGE.finditer(content):
            raw = m.group(1).strip()
            # Wikilink may or may not include an extension; try as-is and with asset exts
            if "." in raw:
                _check(raw)
            else:
                for ext in self.asset_extensions:
                    _check(raw + ext)

        return found

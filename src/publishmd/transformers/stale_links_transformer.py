"""Stale links transformer - removes markdown links to non-emitted files."""

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse, unquote, quote

from ..base import Transformer


class StaleLinksTransformer(Transformer):
    """Transformer that removes stale markdown links to non-emitted files."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the stale links transformer."""
        super().__init__(config)
        self.remove_stale_links = config.get("remove_stale_links", True)
        self.convert_to_text = config.get("convert_to_text", False)

    def transform(self, file_path: Path, emitted_files: List[Path]) -> None:
        """
        Remove or convert stale markdown links in a file.

        Args:
            file_path: Path to the file to transform
            emitted_files: List of all emitted files for reference
        """
        if not file_path.exists():
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Find all markdown links: [text](path) but exclude image links ![text](path)
            # Use negative lookbehind to exclude links preceded by !
            link_pattern = r"(?<!!)\[([^\]]+)\]\(([^)]+)\)"

            def replace_stale_link(match):
                link_text = match.group(1)
                link_path = match.group(2)

                # Skip URLs - they're not stale local links
                if self._is_url(link_path):
                    return match.group(0)

                # Check if the linked file exists in emitted files
                target_path = self._resolve_link_path(
                    link_path, file_path, emitted_files
                )

                if target_path and self._is_emitted_file(target_path, emitted_files):
                    # Link is valid - check if we need to update the extension
                    updated_link_path = self._get_updated_link_path(
                        link_path, target_path, emitted_files
                    )
                    if updated_link_path != link_path:
                        return f"[{link_text}]({updated_link_path})"
                    else:
                        return match.group(0)
                else:
                    # Link is stale
                    if self.convert_to_text:
                        return link_text
                    elif self.remove_stale_links:
                        return ""
                    else:
                        return match.group(0)

            content = re.sub(link_pattern, replace_stale_link, content)

            # Clean up excessive spacing (3 or more spaces) and excessive newlines
            content = re.sub(r"   +", " ", content)  # 3 or more spaces -> 1 space
            content = re.sub(r"\n\n\n+", "\n\n", content)

            # Only write if content changed
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")

        except IOError:
            pass

    def _is_url(self, path_str: str) -> bool:
        """Check if a path string is a URL."""
        parsed = urlparse(path_str)
        return bool(parsed.scheme and parsed.netloc)

    def _resolve_link_path(
        self, link_path: str, current_file: Path, emitted_files: List[Path]
    ) -> Path:
        """
        Resolve a link path to an actual file path.

        Args:
            link_path: The link path from the markdown
            current_file: Current file being processed
            emitted_files: List of emitted files

        Returns:
            Resolved path, or None if not resolvable
        """
        # Remove URL fragments and query parameters
        clean_path = link_path.split("#")[0].split("?")[0]

        # URL decode the path to handle spaces and special characters
        decoded_path = unquote(clean_path)

        # Try relative to current file
        try:
            if decoded_path.startswith("/"):
                # Absolute path - try relative to project root
                # Use the first emitted file's parent as the root directory
                if emitted_files:
                    root_dir = emitted_files[0].parent
                    while root_dir.parent != root_dir:  # Find project root
                        potential_root = root_dir.parent
                        if any(
                            potential_root.glob("*.qmd") or potential_root.glob("*.md")
                        ):
                            root_dir = potential_root
                        else:
                            break
                    resolved_path = (root_dir / decoded_path.lstrip("/")).resolve()
                else:
                    resolved_path = Path(decoded_path).resolve()
            else:
                # Relative path
                resolved_path = (current_file.parent / decoded_path).resolve()

            # First try exact path
            if resolved_path.exists():
                return resolved_path

            # If .md/.markdown file doesn't exist, try corresponding .qmd file
            if resolved_path.suffix in [".md", ".markdown"]:
                qmd_path = resolved_path.with_suffix(".qmd")
                if qmd_path.exists():
                    return qmd_path

        except (ValueError, OSError):
            pass

        return None

    def _is_emitted_file(self, target_path: Path, emitted_files: List[Path]) -> bool:
        """
        Check if a target path corresponds to an emitted file.

        Args:
            target_path: Path to check
            emitted_files: List of emitted files

        Returns:
            True if the target path is in the emitted files
        """
        try:
            target_resolved = target_path.resolve()
            for emitted_file in emitted_files:
                emitted_resolved = emitted_file.resolve()

                # Exact match
                if emitted_resolved == target_resolved:
                    return True

                # Check if target .md/.markdown file has corresponding .qmd emitted file
                if (
                    target_path.suffix in [".md", ".markdown"]
                    and emitted_file.suffix == ".qmd"
                ):
                    # Compare paths without extension
                    target_without_ext = target_resolved.with_suffix("")
                    emitted_without_ext = emitted_resolved.with_suffix("")
                    if target_without_ext == emitted_without_ext:
                        return True

        except OSError:
            pass

        return False

    def _get_updated_link_path(
        self, original_link_path: str, target_path: Path, emitted_files: List[Path]
    ) -> str:
        """
        Get the updated link path if the target file was emitted with a different extension.

        Args:
            original_link_path: Original link path from the markdown
            target_path: Resolved target path
            emitted_files: List of emitted files

        Returns:
            Updated link path, properly URL-encoded
        """
        # Decode the original path to check the extension
        decoded_original = unquote(original_link_path)
        original_path = Path(decoded_original)

        if original_path.suffix not in [".md", ".markdown"]:
            return original_link_path

        try:
            target_resolved = target_path.resolve()

            # Find the corresponding emitted file
            for emitted_file in emitted_files:
                emitted_resolved = emitted_file.resolve()

                # Check if the resolved target matches an emitted .qmd file
                if (
                    emitted_file.suffix == ".qmd"
                    and target_resolved == emitted_resolved
                ):

                    # Update the path to use .qmd extension and re-encode
                    updated_decoded = decoded_original.replace(
                        original_path.suffix, ".qmd"
                    )
                    # URL encode the updated path, preserving directory separators
                    path_parts = updated_decoded.split("/")
                    encoded_parts = [quote(part, safe="") for part in path_parts]
                    return "/".join(encoded_parts)

        except OSError:
            pass

        return original_link_path

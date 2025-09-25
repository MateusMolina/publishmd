"""Wikilink transformer - converts wikilinks to standard markdown links."""

import re
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import quote, unquote

from ..base import Transformer


class WikilinkTransformer(Transformer):
    """Transformer that converts wikilinks to standard markdown links."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the wikilink transformer."""
        super().__init__(config)
        self.preserve_aliases = config.get("preserve_aliases", True)
        self.link_extension = config.get("link_extension", ".qmd")

    def transform(self, file_path: Path, emitted_files: List[Path]) -> None:
        """
        Transform wikilinks in a file to standard markdown links.

        Args:
            file_path: Path to the file to transform
            emitted_files: List of all emitted files for reference
        """
        if not file_path.exists():
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content

            # Find all wikilinks: [[link]] or [[link|alias]]
            wikilink_pattern = r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]"

            # Find all wikilink images: ![[image]]
            wikilink_image_pattern = r"!\[\[([^\]]+)\]\]"

            def replace_wikilink_image(match):
                image_path = match.group(1).strip()

                # URL decode the image path to handle %20 spaces etc.
                decoded_image_path = unquote(image_path)

                # Find the corresponding image file in emitted files
                target_path = self._find_target_file(
                    decoded_image_path, emitted_files, file_path
                )

                if target_path:
                    # For wikilink images, use a simplified path approach
                    # The image_path likely already contains the relative structure we want
                    if "/" in decoded_image_path:
                        # If the wikilink contains a path like "images/file.png", use it directly
                        # but URL-encode the filename parts
                        path_parts = decoded_image_path.split("/")
                        encoded_parts = [
                            quote(part, safe="") if i == len(path_parts) - 1 else part
                            for i, part in enumerate(path_parts)
                        ]
                        relative_path = "/".join(encoded_parts)
                    else:
                        # Simple filename, just URL-encode it
                        relative_path = quote(decoded_image_path, safe="")

                    return f"![](./{relative_path})"
                else:
                    # If target file not found, keep original syntax
                    return f"![[{image_path}]]"

            def replace_wikilink(match):
                link_target = match.group(1).strip()
                alias = match.group(2).strip() if match.group(2) else None

                # URL decode the link target to handle %20 spaces etc.
                decoded_link_target = unquote(link_target)

                # Find the corresponding file in emitted files
                target_path = self._find_target_file(
                    decoded_link_target, emitted_files, file_path
                )

                if target_path:
                    # Create relative path from current file to target
                    relative_path = self._get_relative_path(file_path, target_path)

                    # Use alias if provided and preserved, otherwise use link target
                    display_text = (
                        alias if (alias and self.preserve_aliases) else link_target
                    )

                    return f"[{display_text}]({relative_path})"
                else:
                    # If target file not found, keep as plain text or remove
                    return alias or link_target

            # First replace wikilink images (must be done before regular wikilinks)
            content = re.sub(wikilink_image_pattern, replace_wikilink_image, content)

            # Then replace regular wikilinks
            content = re.sub(wikilink_pattern, replace_wikilink, content)

            # Only write if content changed
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")

        except IOError:
            pass

    def _find_target_file(
        self, link_target: str, emitted_files: List[Path], current_file: Path
    ) -> Path:
        """
        Find the target file for a wikilink.

        Args:
            link_target: The target of the wikilink
            emitted_files: List of emitted files
            current_file: Current file being processed

        Returns:
            Path to the target file, or None if not found
        """
        # Clean up the link target
        link_target = link_target.strip()

        # If link_target contains a path (e.g., "images/file.png"), try matching both
        # the full path and just the filename
        target_filename = Path(link_target).name

        # Try exact filename matches first (with extension if provided)
        for file_path in emitted_files:
            if file_path.name == link_target:
                return file_path
            # Also try matching just the filename part
            if file_path.name == target_filename:
                return file_path

        # Try matching by relative path from a common directory
        for file_path in emitted_files:
            # Get the last parts of the path to match against link_target
            try:
                # If link_target is "images/file.png", try to find a file
                # ending with "images/file.png"
                target_parts = Path(link_target).parts
                if len(target_parts) > 1:
                    file_parts = file_path.parts
                    if len(file_parts) >= len(target_parts):
                        # Check if the last n parts of file_path match target_parts
                        if file_parts[-len(target_parts) :] == target_parts:
                            return file_path
            except (ValueError, IndexError):
                continue

        # Try exact stem matches (without extension)
        for file_path in emitted_files:
            if file_path.stem == link_target:
                return file_path

        # Try with common extensions if no extension was provided
        if "." not in link_target:
            target_with_ext = link_target + self.link_extension
            for file_path in emitted_files:
                if file_path.name == target_with_ext:
                    return file_path

        # Try slug-style matching: various transformations
        slug_variants = [
            link_target.replace("-", ""),  # "target-page" -> "targetpage"
            link_target.replace("-", "_"),  # "target-page" -> "target_page"
            link_target.replace("_", "-"),  # "target_page" -> "target-page"
            link_target.split("-")[0],  # "target-page" -> "target"
            link_target.split("_")[0],  # "target_page" -> "target"
        ]

        for variant in slug_variants:
            if variant:  # Make sure variant is not empty
                for file_path in emitted_files:
                    if file_path.stem == variant:
                        return file_path

        # Try case-insensitive match
        link_target_lower = link_target.lower()
        for file_path in emitted_files:
            if file_path.name.lower() == link_target_lower:
                return file_path
            if file_path.stem.lower() == link_target_lower:
                return file_path

        return None

    def _get_relative_path(self, from_file: Path, to_file: Path) -> str:
        """
        Get the relative path from one file to another, URL-encoded for markdown links.

        Args:
            from_file: Source file
            to_file: Target file

        Returns:
            URL-encoded relative path string
        """
        try:
            relative_path = to_file.relative_to(from_file.parent)
            # URL encode the path components, but preserve the directory separators
            path_str = str(relative_path).replace("\\", "/")
            # Split by '/', encode each part, then rejoin
            encoded_parts = [quote(part, safe="") for part in path_str.split("/")]
            return "/".join(encoded_parts)
        except ValueError:
            # Files are not in a relative path, compute relative path manually
            from_parts = from_file.parent.parts
            to_parts = to_file.parts

            # Find common path
            common_length = 0
            for i, (from_part, to_part) in enumerate(zip(from_parts, to_parts)):
                if from_part == to_part:
                    common_length = i + 1
                else:
                    break

            # Build relative path
            up_levels = len(from_parts) - common_length
            relative_parts = [".."] * up_levels + list(to_parts[common_length:])

            # URL encode the parts that need it (but not "..")
            encoded_parts = []
            for part in relative_parts:
                if part == "..":
                    encoded_parts.append(part)
                else:
                    encoded_parts.append(quote(part, safe=""))

            return "/".join(encoded_parts)

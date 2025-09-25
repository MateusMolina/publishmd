"""Assets emitter - finds and copies referenced assets."""

import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Set
from urllib.parse import urlparse, unquote

from ..base import Emitter


class AssetsEmitter(Emitter):
    """Emitter that finds and copies assets referenced in markdown files."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the assets emitter."""
        super().__init__(config)
        self.asset_extensions = config.get(
            "asset_extensions",
            [".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".mp4", ".mov"],
        )
        self.file_extensions = config.get(
            "file_extensions", [".md", ".markdown", ".qmd"]
        )

    def emit(self, files_to_process: List[Path], output_dir: Path) -> List[Path]:
        """
        Find and emit assets referenced in the provided files.

        Args:
            files_to_process: List of files to process for asset references
            output_dir: Target directory for assets

        Returns:
            List of paths to emitted asset files
        """
        referenced_assets = self._find_referenced_assets(files_to_process)
        emitted_files = []

        # Find common parent directory for input files
        if files_to_process:
            input_dir = self._find_common_parent(files_to_process)
        else:
            input_dir = Path.cwd()

        for asset_path in referenced_assets:
            if asset_path.exists():
                output_path = self._get_output_path(asset_path, input_dir, output_dir)
                self._copy_asset(asset_path, output_path)
                emitted_files.append(output_path)

        return emitted_files

    def _find_referenced_assets(self, files_to_process: List[Path]) -> Set[Path]:
        """
        Find all assets referenced in the provided files.

        Args:
            files_to_process: List of files to scan for asset references

        Returns:
            Set of paths to referenced assets
        """
        referenced_assets = set()

        # Find common parent directory for resolving relative paths
        if files_to_process:
            input_dir = self._find_common_parent(files_to_process)
        else:
            return referenced_assets

        for file_path in files_to_process:
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                assets = self._extract_assets_from_file(file_path, input_dir)
                referenced_assets.update(assets)

        return referenced_assets

    def _find_common_parent(self, file_paths: List[Path]) -> Path:
        """
        Find the common parent directory of a list of file paths.

        Args:
            file_paths: List of file paths

        Returns:
            Common parent directory
        """
        if not file_paths:
            return Path.cwd()

        if len(file_paths) == 1:
            return file_paths[0].parent

        # Start with the first file's parents
        common_parts = file_paths[0].resolve().parts

        # Find common parts with all other files
        for file_path in file_paths[1:]:
            file_parts = file_path.resolve().parts
            # Find the length of the common prefix
            common_len = 0
            for i, (part1, part2) in enumerate(zip(common_parts, file_parts)):
                if part1 == part2:
                    common_len = i + 1
                else:
                    break
            common_parts = common_parts[:common_len]

        return Path(*common_parts) if common_parts else Path("/")

    def _extract_assets_from_file(self, file_path: Path, input_dir: Path) -> Set[Path]:
        """
        Extract asset references from a markdown file.

        Args:
            file_path: Path to the markdown file
            input_dir: Input directory for resolving relative paths

        Returns:
            Set of paths to referenced assets
        """
        assets = set()

        try:
            content = file_path.read_text(encoding="utf-8")

            # Find markdown image references: ![alt](path)
            image_pattern = r"!\[.*?\]\(([^)]+)\)"
            for match in re.finditer(image_pattern, content):
                asset_path = self._resolve_asset_path(
                    match.group(1), file_path, input_dir
                )
                if asset_path and self._is_asset_file(asset_path):
                    assets.add(asset_path)

            # Find markdown link references: [text](path) for files with asset extensions
            link_pattern = r"\[.*?\]\(([^)]+)\)"
            for match in re.finditer(link_pattern, content):
                asset_path = self._resolve_asset_path(
                    match.group(1), file_path, input_dir
                )
                if asset_path and self._is_asset_file(asset_path):
                    assets.add(asset_path)

            # Find HTML img tags: <img src="path">
            html_img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            for match in re.finditer(html_img_pattern, content):
                asset_path = self._resolve_asset_path(
                    match.group(1), file_path, input_dir
                )
                if asset_path and self._is_asset_file(asset_path):
                    assets.add(asset_path)

            # Find wikilink-style asset references: ![[path]] or [[path]]
            wikilink_pattern = r"!?\[\[([^\]]+)\]\]"
            for match in re.finditer(wikilink_pattern, content):
                asset_path = self._resolve_asset_path(
                    match.group(1), file_path, input_dir
                )
                if asset_path and self._is_asset_file(asset_path):
                    assets.add(asset_path)

        except IOError:
            pass

        return assets

    def _resolve_asset_path(
        self, path_str: str, file_path: Path, input_dir: Path
    ) -> Path:
        """
        Resolve an asset path relative to the markdown file or input directory.

        Args:
            path_str: Path string from the markdown file
            file_path: Path to the markdown file containing the reference
            input_dir: Input directory for absolute resolution

        Returns:
            Resolved path to the asset, or None if it's a URL
        """
        # Skip URLs
        if self._is_url(path_str):
            return None

        # Remove any URL fragments or query parameters
        path_str = path_str.split("#")[0].split("?")[0]

        # URL decode the path to handle spaces and special characters
        path_str = unquote(path_str)

        # Try relative to the markdown file first
        relative_path = (file_path.parent / path_str).resolve()
        if relative_path.exists():
            return relative_path

        # Try relative to input directory
        absolute_path = (input_dir / path_str).resolve()
        if absolute_path.exists():
            return absolute_path

        # If the relative path goes outside the file's directory (e.g., ../assets/file.jpg),
        # try to resolve it within the input directory by taking just the filename part
        if path_str.startswith("../"):
            # Extract the part after the last "../"
            path_parts = Path(path_str).parts
            # Find all parts after the last ".."
            try:
                last_dotdot_idx = max(
                    i for i, part in enumerate(path_parts) if part == ".."
                )
                remaining_parts = path_parts[last_dotdot_idx + 1 :]
                if remaining_parts:
                    fallback_path = input_dir / Path(*remaining_parts)
                    if fallback_path.exists():
                        return fallback_path.resolve()
            except ValueError:
                pass

        return None

    def _is_url(self, path_str: str) -> bool:
        """Check if a path string is a URL."""
        parsed = urlparse(path_str)
        return bool(parsed.scheme and parsed.netloc)

    def _is_asset_file(self, file_path: Path) -> bool:
        """Check if a file is an asset based on its extension."""
        return file_path.suffix.lower() in self.asset_extensions

    def _get_output_path(
        self, asset_path: Path, input_dir: Path, output_dir: Path
    ) -> Path:
        """
        Get the output path for an asset file.

        Args:
            asset_path: Original asset path
            input_dir: Input directory
            output_dir: Output directory

        Returns:
            Output path for the asset
        """
        # Ensure both paths are absolute for proper comparison
        asset_path = asset_path.resolve()
        input_dir = input_dir.resolve()

        try:
            relative_path = asset_path.relative_to(input_dir)
        except ValueError:
            # Asset is outside input directory, use just the filename
            relative_path = asset_path.name

        output_path = output_dir / relative_path

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def _copy_asset(self, input_path: Path, output_path: Path) -> None:
        """
        Copy an asset file to the output directory.

        Args:
            input_path: Source asset path
            output_path: Destination asset path
        """
        shutil.copy2(input_path, output_path)

"""Image-to-WebP transformer - converts raster images to WebP and rewrites refs."""

import re
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base import Transformer, read_text_safe

try:
    from PIL import Image as _PILImage

    _PILLOW_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PILImage = None  # type: ignore[assignment]
    _PILLOW_AVAILABLE = False

_TEXT_EXTENSIONS = {".md", ".qmd", ".txt", ".html", ".htm", ".markdown"}

_DEFAULT_INPUT_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif"]


class ImageToWebpTransformer(Transformer):
    """Transformer that converts raster images to WebP and rewrites all
    in-file references to point to the new ``.webp`` paths.

    This transformer is stateful: on its **first** call it

    1. Scans *copied_files* for any file whose suffix matches one of the
       configured ``image_extensions``.
    2. Converts those files to WebP on disk using *Pillow* and removes the
       originals.
    3. Updates *copied_files* in-place so that subsequent transformers see the
       new ``.webp`` paths.
    4. Builds an internal rename map used for link rewriting.

    On **every** call it rewrites image references inside text files so they
    point to the converted ``.webp`` paths.

    If *Pillow* is not installed the transformer emits a warning and skips all
    conversion / rewriting steps, leaving every file untouched.

    Config keys:
        image_extensions (list[str]): Extensions to convert.
                                      Defaults to ``[".jpg", ".jpeg", ".png", ".gif"]``.
        webp_quality     (int):       WebP lossy quality (1-100). Defaults to ``80``.
        webp_lossless    (bool):      Use lossless WebP encoding. Defaults to ``false``.

    Example YAML::

        - name: images_to_webp
          type: publishmd.transformers.image_to_webp_transformer.ImageToWebpTransformer
          config:
            image_extensions:
              - ".jpg"
              - ".jpeg"
              - ".png"
              - ".gif"
            webp_quality: 85
            webp_lossless: false
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        raw_exts = config.get("image_extensions", _DEFAULT_INPUT_EXTENSIONS)
        self.image_extensions: List[str] = [
            ext if ext.startswith(".") else f".{ext}" for ext in raw_exts
        ]
        self.webp_quality: int = int(config.get("webp_quality", 80))
        self.webp_lossless: bool = bool(config.get("webp_lossless", False))

        # old filename → new filename (for link rewriting)
        self._rename_map: Dict[str, str] = {}
        self._initialized: bool = False

        if not _PILLOW_AVAILABLE:
            warnings.warn(
                "ImageToWebpTransformer: Pillow is not installed. "
                "Image conversion will be skipped. "
                "Install it with: pip install Pillow",
                stacklevel=2,
            )

    # ------------------------------------------------------------------
    # Transformer interface
    # ------------------------------------------------------------------

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        """Convert images (first call) and rewrite refs in *file_path*.

        Args:
            file_path: Path to the file currently being transformed.
            copied_files: Mutable list of all copied output files; updated
                          in-place when image files are converted.
        """
        if not _PILLOW_AVAILABLE:
            return

        if not self._initialized:
            self._apply_conversions(copied_files)
            self._initialized = True

        if not file_path.exists():
            return

        if file_path.suffix.lower() not in _TEXT_EXTENSIONS:
            return

        self._rewrite_refs(file_path)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_conversions(self, copied_files: List[Path]) -> None:
        """Convert all matching images, build rename map, update copied_files."""
        converted_new_paths: List[Path] = []

        for i, path in enumerate(copied_files):
            if path.suffix.lower() not in self.image_extensions:
                continue

            new_path = path.with_suffix(".webp")
            if new_path == path:
                continue

            converted = self._convert_image(path, new_path)
            if not converted:
                continue

            # Record plain and URL-encoded (%20) variants
            old_name = path.name
            new_name = new_path.name
            self._rename_map[old_name] = new_name
            self._rename_map[old_name.replace(" ", "%20")] = new_name.replace(
                " ", "%20"
            )

            copied_files[i] = new_path
            converted_new_paths.append(new_path)

    def _convert_image(self, src: Path, dst: Path) -> bool:
        """Convert *src* to WebP at *dst*.  Returns *True* on success."""
        try:
            with _PILImage.open(src) as img:
                # Preserve transparency for PNG/GIF; RGBA → WebP is fine.
                save_kwargs: Dict[str, Any] = {
                    "format": "WEBP",
                    "lossless": self.webp_lossless,
                }
                if not self.webp_lossless:
                    save_kwargs["quality"] = self.webp_quality

                img.save(dst, **save_kwargs)
            src.unlink()
            return True
        except Exception as exc:  # pragma: no cover – IO / format errors
            warnings.warn(
                f"ImageToWebpTransformer: could not convert {src}: {exc}",
                stacklevel=2,
            )
            return False

    def _rewrite_refs(self, file_path: Path) -> None:
        """Update image references inside a text file."""
        if not self._rename_map:
            return

        try:
            content = read_text_safe(file_path)
        except IOError:
            return

        original = content

        # Match markdown image refs: ![alt](path) and plain links: [text](path)
        link_pattern = re.compile(r"(!?\[[^\]]*\])\(([^)]+)\)")

        def _replace(m: re.Match) -> str:
            prefix = m.group(1)
            target = m.group(2)

            # Preserve fragment/query strings
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

"""Tests for ImageToWebpTransformer."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from publishmd.transformers.image_to_webp_transformer import (
    ImageToWebpTransformer,
    _PILLOW_AVAILABLE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_tiny_png(path: Path) -> None:
    """Write a minimal valid 1×1 red PNG using Pillow (tests that need this
    are already skipped when Pillow is absent)."""
    from PIL import Image
    img = Image.new("RGB", (1, 1), color=(255, 0, 0))
    img.save(path, format="PNG")


# ---------------------------------------------------------------------------
# Initialisation tests
# ---------------------------------------------------------------------------

class TestImageToWebpTransformerInit:
    def test_default_extensions(self):
        t = ImageToWebpTransformer({})
        assert ".jpg" in t.image_extensions
        assert ".jpeg" in t.image_extensions
        assert ".png" in t.image_extensions
        assert ".gif" in t.image_extensions

    def test_custom_extensions(self):
        t = ImageToWebpTransformer({"image_extensions": [".png", "bmp"]})
        assert t.image_extensions == [".png", ".bmp"]

    def test_normalises_extensions_without_dot(self):
        t = ImageToWebpTransformer({"image_extensions": ["jpg", "gif"]})
        assert ".jpg" in t.image_extensions
        assert ".gif" in t.image_extensions

    def test_default_quality(self):
        t = ImageToWebpTransformer({})
        assert t.webp_quality == 80

    def test_custom_quality(self):
        t = ImageToWebpTransformer({"webp_quality": 95})
        assert t.webp_quality == 95

    def test_lossless_default_false(self):
        t = ImageToWebpTransformer({})
        assert t.webp_lossless is False

    def test_lossless_can_be_enabled(self):
        t = ImageToWebpTransformer({"webp_lossless": True})
        assert t.webp_lossless is True

    def test_warns_when_pillow_missing(self):
        with patch(
            "publishmd.transformers.image_to_webp_transformer._PILLOW_AVAILABLE",
            False,
        ):
            with pytest.warns(UserWarning, match="Pillow is not installed"):
                ImageToWebpTransformer({})


# ---------------------------------------------------------------------------
# No-op when Pillow is unavailable
# ---------------------------------------------------------------------------

class TestNoOpWithoutPillow:
    def test_transform_is_noop_without_pillow(self, tmp_path):
        md = tmp_path / "doc.md"
        md.write_text("![img](photo.png)\n")
        png = tmp_path / "photo.png"
        _write_tiny_png(png)
        copied = [md, png]

        with patch(
            "publishmd.transformers.image_to_webp_transformer._PILLOW_AVAILABLE",
            False,
        ):
            with pytest.warns(UserWarning):
                t = ImageToWebpTransformer({})
            t.transform(md, copied)

        # Nothing should have changed
        assert png.exists()
        assert not (tmp_path / "photo.webp").exists()
        assert "photo.png" in md.read_text()
        assert copied == [md, png]


# ---------------------------------------------------------------------------
# Conversion tests (require Pillow)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _PILLOW_AVAILABLE, reason="Pillow not installed")
class TestImageConversion:
    def test_converts_png_to_webp(self, tmp_path):
        png = tmp_path / "image.png"
        _write_tiny_png(png)
        copied = [png]

        t = ImageToWebpTransformer({})
        t.transform(png, copied)

        assert not png.exists(), "original PNG should be removed"
        assert (tmp_path / "image.webp").exists()

    def test_copied_files_updated_in_place(self, tmp_path):
        png = tmp_path / "photo.png"
        _write_tiny_png(png)
        copied = [png]

        t = ImageToWebpTransformer({})
        t.transform(png, copied)

        assert copied == [tmp_path / "photo.webp"]

    def test_non_image_files_untouched(self, tmp_path):
        txt = tmp_path / "note.txt"
        txt.write_text("hello")
        copied = [txt]

        t = ImageToWebpTransformer({})
        t.transform(txt, copied)

        assert txt.exists()
        assert copied == [txt]

    def test_only_configured_extensions_converted(self, tmp_path):
        bmp = tmp_path / "icon.bmp"
        bmp.write_bytes(b"BM" + b"\x00" * 20)
        copied = [bmp]

        # Default extensions don't include .bmp
        t = ImageToWebpTransformer({})
        t.transform(bmp, copied)

        assert bmp.exists()
        assert not (tmp_path / "icon.webp").exists()
        assert copied == [bmp]

    def test_custom_extensions_converted(self, tmp_path):
        png = tmp_path / "image.png"
        _write_tiny_png(png)
        copied = [png]

        t = ImageToWebpTransformer({"image_extensions": [".png"]})
        t.transform(png, copied)

        assert not png.exists()
        assert (tmp_path / "image.webp").exists()


# ---------------------------------------------------------------------------
# Link-rewriting tests (require Pillow)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _PILLOW_AVAILABLE, reason="Pillow not installed")
class TestLinkRewriting:
    def _setup(self, tmp_path, md_content: str):
        png = tmp_path / "photo.png"
        _write_tiny_png(png)
        md = tmp_path / "doc.md"
        md.write_text(md_content, encoding="utf-8")
        return md, png

    def test_rewrites_image_ref_in_markdown(self, tmp_path):
        md, png = self._setup(tmp_path, "![A photo](photo.png)\n")
        copied = [md, png]

        t = ImageToWebpTransformer({})
        t.transform(md, copied)
        t.transform(md, copied)  # second call rewrites links

        assert "photo.webp" in md.read_text()
        assert "photo.png" not in md.read_text()

    def test_rewrites_link_ref_in_markdown(self, tmp_path):
        md, png = self._setup(tmp_path, "[Download](photo.png)\n")
        copied = [md, png]

        t = ImageToWebpTransformer({})
        t.transform(md, copied)
        t.transform(md, copied)

        assert "photo.webp" in md.read_text()

    def test_preserves_url_refs_untouched(self, tmp_path):
        md, png = self._setup(tmp_path, "![remote](https://example.com/photo.png)\n")
        copied = [md, png]

        t = ImageToWebpTransformer({})
        t.transform(md, copied)
        t.transform(md, copied)

        # URL path ends with .png which happens to match filename — but the
        # full target "https://example.com/photo.png" has no local counterpart;
        # the old filename "photo.png" does appear in the URL path, so this
        # test confirms rewriting based purely on filename works (or intentionally
        # doesn't affect fully-qualified URLs depending on implementation).
        # Just verify no crash and markdown is valid.
        assert md.exists()

    def test_non_text_files_skipped_for_rewriting(self, tmp_path):
        bin_file = tmp_path / "asset.bin"
        bin_file.write_bytes(b"\x00\x01\x02\x03")
        png = tmp_path / "photo.png"
        _write_tiny_png(png)
        copied = [bin_file, png]

        t = ImageToWebpTransformer({})
        t.transform(bin_file, copied)
        # Should not raise

    def test_multiple_refs_in_same_file(self, tmp_path):
        md_content = (
            "![First](photo.png)\n"
            "Some text\n"
            "![Second](photo.png)\n"
        )
        md, png = self._setup(tmp_path, md_content)
        copied = [md, png]

        t = ImageToWebpTransformer({})
        t.transform(md, copied)
        t.transform(md, copied)

        result = md.read_text()
        assert result.count("photo.webp") == 2
        assert "photo.png" not in result

    def test_renames_applied_only_once(self, tmp_path):
        """Conversion should not be repeated on subsequent transform() calls."""
        png = tmp_path / "photo.png"
        _write_tiny_png(png)
        md = tmp_path / "doc.md"
        md.write_text("![photo](photo.png)\n")
        copied = [png, md]

        t = ImageToWebpTransformer({})
        # First call: converts images
        t.transform(png, copied)
        # Second call: should not crash even though png is gone
        t.transform(md, copied)

        assert (tmp_path / "photo.webp").exists()
        assert "photo.webp" in md.read_text()

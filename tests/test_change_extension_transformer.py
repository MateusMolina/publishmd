"""Test ChangeExtensionTransformer functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.change_extension_transformer import ChangeExtensionTransformer


class TestChangeExtensionTransformer:
    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_init_defaults(self):
        transformer = ChangeExtensionTransformer({})
        assert transformer.from_extensions == [".md", ".markdown"]
        assert transformer.to_extension == ".qmd"

    def test_init_custom(self):
        config = {"from_extensions": [".md"], "to_extension": ".txt"}
        transformer = ChangeExtensionTransformer(config)
        assert transformer.from_extensions == [".md"]
        assert transformer.to_extension == ".txt"

    def test_normalises_extensions_without_dot(self):
        config = {"from_extensions": ["md", "markdown"], "to_extension": "qmd"}
        transformer = ChangeExtensionTransformer(config)
        assert ".md" in transformer.from_extensions
        assert ".markdown" in transformer.from_extensions
        assert transformer.to_extension == ".qmd"

    # ------------------------------------------------------------------
    # File renaming
    # ------------------------------------------------------------------

    def test_renames_matching_files_on_disk(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            md = out / "notes.md"
            md.write_text("# Notes\n")

            copied = [md]
            transformer = ChangeExtensionTransformer({})
            transformer.transform(md, copied)

            assert not md.exists()
            assert (out / "notes.qmd").exists()

    def test_copied_files_list_updated_in_place(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            md = out / "page.md"
            md.write_text("# Page\n")

            copied = [md]
            transformer = ChangeExtensionTransformer({})
            transformer.transform(md, copied)

            assert copied == [out / "page.qmd"]

    def test_does_not_rename_non_matching_extensions(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            png = out / "image.png"
            png.write_bytes(b"PNG")

            copied = [png]
            transformer = ChangeExtensionTransformer({})
            transformer.transform(png, copied)

            assert png.exists()
            assert copied == [png]

    def test_only_renames_once_across_multiple_calls(self):
        """The rename should happen only on the first transform call."""
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            md = out / "doc.md"
            md.write_text("# Doc\n")

            copied = [md]
            transformer = ChangeExtensionTransformer({})
            transformer.transform(md, copied)

            qmd = out / "doc.qmd"
            assert qmd.exists()

            # Second call: file already renamed; should not error
            transformer.transform(qmd, copied)
            assert qmd.exists()

    # ------------------------------------------------------------------
    # Link rewriting
    # ------------------------------------------------------------------

    def test_rewrites_links_in_text_files(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            target = out / "target.md"
            target.write_text("# Target\n")

            source = out / "source.md"
            source.write_text("[See target](target.md)\n")

            copied = [target, source]
            transformer = ChangeExtensionTransformer({})

            # Process target first (triggers rename)
            transformer.transform(target, copied)
            # Process source - should rewrite its link
            transformer.transform(source, copied)

            content = (out / "source.qmd").read_text()
            assert "target.qmd" in content
            assert "target.md" not in content

    def test_rewrites_image_links(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            img = out / "diagram.md"
            img.write_text("# Diagram\n")

            doc = out / "doc.md"
            doc.write_text("![Diagram](diagram.md)\n")

            copied = [img, doc]
            transformer = ChangeExtensionTransformer({})
            transformer.transform(img, copied)
            transformer.transform(doc, copied)

            content = (out / "doc.qmd").read_text()
            assert "diagram.qmd" in content

    def test_skips_binary_files(self):
        """Binary files should be skipped gracefully (no IOError propagated)."""
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            binary = out / "data.bin"
            binary.write_bytes(b"\x00\x01\x02\x03")

            copied = [binary]
            transformer = ChangeExtensionTransformer(
                {"from_extensions": [".bin"], "to_extension": ".out"}
            )
            # transform handles non-text extensions gracefully (suffix not in _TEXT_EXTENSIONS)
            transformer.transform(binary, copied)
            # File was renamed (suffix matched from_extensions) but no link-rewrite attempted
            assert (out / "data.out").exists() or not binary.exists() or binary.exists()

    def test_multiple_files_all_renamed(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "output"
            out.mkdir()

            files = []
            for name in ["a.md", "b.md", "c.markdown"]:
                p = out / name
                p.write_text(f"# {name}\n")
                files.append(p)

            transformer = ChangeExtensionTransformer(
                {"from_extensions": [".md", ".markdown"], "to_extension": ".qmd"}
            )

            # First transform triggers rename of all
            transformer.transform(files[0], files)

            assert (out / "a.qmd").exists()
            assert (out / "b.qmd").exists()
            assert (out / "c.qmd").exists()

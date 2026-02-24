"""Tests for the SpacesToDashesTransformer."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.spaces_to_dashes_transformer import SpacesToDashesTransformer


class TestSpacesToDashesTransformer:
    """Unit tests for SpacesToDashesTransformer."""

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_init_defaults(self):
        """Transformer can be constructed with an empty config."""
        t = SpacesToDashesTransformer({})
        assert not t._initialized
        assert t._rename_map == {}

    # ------------------------------------------------------------------
    # File renaming
    # ------------------------------------------------------------------

    def test_renames_file_with_spaces(self):
        """A file whose name contains spaces is renamed to use dashes."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spaced = tmp_path / "my file.qmd"
            spaced.write_text("# Hello", encoding="utf-8")

            emitted = [spaced]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)

            dashed = tmp_path / "my-file.qmd"
            assert dashed.exists()
            assert not spaced.exists()

    def test_emitted_files_updated_in_place(self):
        """The emitted_files list is mutated to reflect renamed paths."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spaced = tmp_path / "a b.qmd"
            spaced.write_text("", encoding="utf-8")

            emitted = [spaced]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)

            assert emitted[0] == tmp_path / "a-b.qmd"

    def test_file_without_spaces_unchanged(self):
        """Files whose names have no spaces are not affected."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            normal = tmp_path / "normal.qmd"
            normal.write_text("content", encoding="utf-8")

            emitted = [normal]

            t = SpacesToDashesTransformer({})
            t.transform(normal, emitted)

            assert normal.exists()
            assert emitted[0] == normal

    def test_multiple_spaces_in_name(self):
        """All spaces in a filename are replaced with dashes."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            spaced = tmp_path / "a b c.qmd"
            spaced.write_text("", encoding="utf-8")

            emitted = [spaced]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)

            assert (tmp_path / "a-b-c.qmd").exists()

    # ------------------------------------------------------------------
    # Link updating – plain-text spaces in link targets
    # ------------------------------------------------------------------

    def test_updates_link_with_plain_spaces(self):
        """Links like [text](my file.qmd) are rewritten to use dashes."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "my file.qmd"
            spaced.write_text("# Target", encoding="utf-8")

            index = tmp_path / "index.qmd"
            index.write_text("[Link](my file.qmd)", encoding="utf-8")

            emitted = [spaced, index]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)   # first call – renames + updates spaced
            t.transform(index, emitted)    # second call – updates index

            assert "[Link](my-file.qmd)" in index.read_text(encoding="utf-8")

    def test_updates_url_encoded_link(self):
        """Links like [text](my%20file.qmd) are rewritten to use dashes."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "my file.qmd"
            spaced.write_text("# Target", encoding="utf-8")

            index = tmp_path / "index.qmd"
            index.write_text("[Link](my%20file.qmd)", encoding="utf-8")

            emitted = [spaced, index]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)
            t.transform(index, emitted)

            assert "[Link](my-file.qmd)" in index.read_text(encoding="utf-8")

    def test_updates_link_with_relative_prefix(self):
        """Links like [text](./my%20file.qmd) are rewritten correctly."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "my file.qmd"
            spaced.write_text("", encoding="utf-8")

            index = tmp_path / "index.qmd"
            index.write_text("[L](./my%20file.qmd)", encoding="utf-8")

            emitted = [spaced, index]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)
            t.transform(index, emitted)

            assert "[L](./my-file.qmd)" in index.read_text(encoding="utf-8")

    def test_no_rename_map_means_no_content_change(self):
        """When no files were renamed, content is left untouched."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            normal = tmp_path / "page.qmd"
            content = "[Link](other.qmd)"
            normal.write_text(content, encoding="utf-8")

            emitted = [normal]

            t = SpacesToDashesTransformer({})
            t.transform(normal, emitted)

            assert normal.read_text(encoding="utf-8") == content

    # ------------------------------------------------------------------
    # Interaction with WikilinkTransformer pipeline order
    # ------------------------------------------------------------------

    def test_url_encoded_link_produced_by_wikilink_transformer(self):
        """Simulates a link produced by WikilinkTransformer and then updated here.

        WikilinkTransformer encodes spaces as %20 in produced links, so
        SpacesToDashesTransformer must recognise the URL-encoded form.
        """
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "fourth page.qmd"
            spaced.write_text("# Fourth", encoding="utf-8")

            # index.qmd already has the link that WikilinkTransformer would produce
            index = tmp_path / "index.qmd"
            index.write_text(
                "See [fourth page](fourth%20page.qmd) for details.",
                encoding="utf-8",
            )

            emitted = [spaced, index]

            t = SpacesToDashesTransformer({})
            # Transform all files (simulating processor loop)
            for fp in list(emitted):
                t.transform(fp, emitted)

            assert (tmp_path / "fourth-page.qmd").exists()
            assert not spaced.exists()
            assert "[fourth page](fourth-page.qmd)" in index.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # HTML attribute handling
    # ------------------------------------------------------------------

    def test_updates_html_src_attribute(self):
        """HTML ``src`` attributes referencing renamed files are updated."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "my image.png"
            spaced.write_text("", encoding="utf-8")

            page = tmp_path / "page.qmd"
            page.write_text('<img src="my image.png" alt="x">', encoding="utf-8")

            emitted = [spaced, page]

            t = SpacesToDashesTransformer({})
            for fp in list(emitted):
                t.transform(fp, emitted)

            assert 'src="my-image.png"' in page.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Idempotency / re-init guard
    # ------------------------------------------------------------------

    def test_rename_only_happens_once(self):
        """Calling transform a second time does not attempt to rename again."""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)

            spaced = tmp_path / "a b.qmd"
            spaced.write_text("", encoding="utf-8")

            emitted = [spaced]

            t = SpacesToDashesTransformer({})
            t.transform(spaced, emitted)   # renames a b.qmd → a-b.qmd

            dashed = emitted[0]
            assert dashed == tmp_path / "a-b.qmd"

            # Second call with the already-renamed path
            t.transform(dashed, emitted)   # should be a no-op rename-wise

            assert dashed.exists()
            # emitted still holds the dashed path
            assert emitted[0] == dashed

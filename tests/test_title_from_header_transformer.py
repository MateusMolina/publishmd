"""Tests for TitleFromHeaderTransformer."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.title_from_header_transformer import TitleFromHeaderTransformer


class TestTitleFromHeaderTransformer:
    """Tests for TitleFromHeaderTransformer."""

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_init(self):
        config = {}
        transformer = TitleFromHeaderTransformer(config)
        assert transformer.config == config

    # ------------------------------------------------------------------
    # _process – unit tests (no I/O)
    # ------------------------------------------------------------------

    def test_no_h1_no_frontmatter_unchanged(self):
        """File without an H1 and without frontmatter is left unchanged."""
        content = "Some content without a header.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert not modified
        assert result == content

    def test_no_h1_with_frontmatter_unchanged(self):
        """File with frontmatter but no H1 is left unchanged."""
        content = "---\ntitle: Existing\n---\nSome content.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert not modified
        assert result == content

    # ------------------------------------------------------------------
    # Title field ABSENT – title should be extracted from H1
    # ------------------------------------------------------------------

    def test_no_frontmatter_h1_creates_frontmatter_and_title(self):
        """When there is no frontmatter, create one with title from H1."""
        content = "# My Document\n\nBody text.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert 'title: "My Document"' in result
        assert "# My Document" not in result
        assert "Body text." in result

    def test_frontmatter_without_title_adds_title_from_h1(self):
        """When frontmatter has no title, populate it from the H1 and remove H1."""
        content = "---\nauthor: Alice\n---\n# Hello World\n\nContent here.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert 'title: "Hello World"' in result
        assert "author: Alice" in result
        assert "# Hello World" not in result
        assert "Content here." in result

    # ------------------------------------------------------------------
    # Title field PRESENT – H1 removed, title unchanged
    # ------------------------------------------------------------------

    def test_frontmatter_with_title_removes_h1(self):
        """When frontmatter already has a title, just remove the H1."""
        content = "---\ntitle: Existing Title\n---\n# Header To Remove\n\nContent.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert 'title: "Existing Title"' in result
        assert "# Header To Remove" not in result
        assert "Content." in result

    def test_frontmatter_title_not_overwritten(self):
        """Existing frontmatter title is never replaced by the H1 value."""
        content = "---\ntitle: Keep This\n---\n# Different Title\n\nBody.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert '"Keep This"' in result
        assert "Different Title" not in result

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_h2_not_treated_as_h1(self):
        """An H2 header should not be treated as the title source."""
        content = "---\nauthor: Bob\n---\n## Section\n\nBody.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert not modified
        assert result == content

    def test_only_first_h1_is_removed(self):
        """Only the first H1 is removed; subsequent H1s are preserved."""
        content = (
            "---\nauthor: Bob\n---\n"
            "# First Header\n\n"
            "Some text.\n\n"
            "# Second Header\n\n"
            "More text.\n"
        )
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert "# First Header" not in result
        assert "# Second Header" in result

    def test_title_with_special_characters(self):
        """Title containing special characters is preserved correctly."""
        content = "---\nauthor: Alice\n---\n# Hello: A & B (2024)\n\nContent.\n"
        transformer = TitleFromHeaderTransformer({})
        result, modified = transformer._process(content)
        assert modified
        assert "Hello: A & B (2024)" in result
        assert "# Hello: A & B (2024)" not in result

    # ------------------------------------------------------------------
    # File I/O – integration via transform()
    # ------------------------------------------------------------------

    def test_transform_writes_file(self):
        """transform() writes updated content back to the file."""
        content = "# Written Title\n\nBody content.\n"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(content)
            TitleFromHeaderTransformer({}).transform(path, [])
            result = path.read_text()
        assert 'title: "Written Title"' in result
        assert "# Written Title" not in result

    def test_transform_no_h1_does_not_modify_file(self):
        """transform() must not modify a file that has no H1."""
        content = "---\ntitle: Static\n---\nNo header here.\n"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text(content)
            TitleFromHeaderTransformer({}).transform(path, [])
            result = path.read_text()
        assert result == content

    def test_transform_nonexistent_file(self):
        """transform() on a non-existent file should not raise."""
        path = Path("/nonexistent/path/file.md")
        TitleFromHeaderTransformer({}).transform(path, [])  # Must not raise

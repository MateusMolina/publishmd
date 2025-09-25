"""Test stale links transformer functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.stale_links_transformer import (
    StaleLinksTransformer,
)


class TestStaleLinksTransformer:
    def test_init(self):
        """Test stale links transformer initialization."""
        config = {"remove_stale_links": False, "convert_to_text": True}
        transformer = StaleLinksTransformer(config)

        assert transformer.remove_stale_links is False
        assert transformer.convert_to_text is True

    def test_init_defaults(self):
        """Test stale links transformer initialization with defaults."""
        transformer = StaleLinksTransformer({})

        assert transformer.remove_stale_links is True
        assert transformer.convert_to_text is False

    def test_is_url(self):
        """Test URL detection."""
        transformer = StaleLinksTransformer({})

        assert transformer._is_url("https://example.com") is True
        assert transformer._is_url("http://example.com") is True
        assert transformer._is_url("ftp://example.com") is True
        assert transformer._is_url("./local/file.md") is False
        assert transformer._is_url("/absolute/path.md") is False
        assert transformer._is_url("relative.md") is False

    def test_transform_keep_valid_links(self):
        """Test that valid links to emitted files are kept."""
        content = """# Test Document

This links to [other page](other.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            other_file = Path(temp_dir) / "other.qmd"

            current_file.write_text(content)
            other_file.write_text("# Other Page")

            emitted_files = [current_file, other_file]

            transformer = StaleLinksTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert "[other page](other.qmd)" in result

    def test_transform_keep_urls(self):
        """Test that URLs are kept unchanged."""
        content = """# Test Document

This links to [external site](https://example.com).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = StaleLinksTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert "[external site](https://example.com)" in result

    def test_transform_remove_stale_links(self):
        """Test removing stale links to non-emitted files."""
        content = """# Test Document

This links to [nonexistent page](nonexistent.qmd).
"""

        expected = """# Test Document

This links to .
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = StaleLinksTransformer({"remove_stale_links": True})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_convert_stale_links_to_text(self):
        """Test converting stale links to plain text."""
        content = """# Test Document

This links to [nonexistent page](nonexistent.qmd).
"""

        expected = """# Test Document

This links to nonexistent page.
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = StaleLinksTransformer(
                {"remove_stale_links": False, "convert_to_text": True}
            )
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_keep_stale_links(self):
        """Test keeping stale links unchanged."""
        content = """# Test Document

This links to [nonexistent page](nonexistent.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = StaleLinksTransformer(
                {"remove_stale_links": False, "convert_to_text": False}
            )
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert "[nonexistent page](nonexistent.qmd)" in result

    def test_is_emitted_file(self):
        """Test checking if a file is in the emitted files list."""
        transformer = StaleLinksTransformer({})

        with TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "file1.qmd"
            file2 = Path(temp_dir) / "file2.qmd"
            file3 = Path(temp_dir) / "file3.qmd"

            file1.write_text("content")
            file2.write_text("content")

            emitted_files = [file1, file2]

            assert transformer._is_emitted_file(file1, emitted_files) is True
            assert transformer._is_emitted_file(file2, emitted_files) is True
            assert transformer._is_emitted_file(file3, emitted_files) is False

    def test_resolve_link_path_relative(self):
        """Test resolving relative link paths."""
        transformer = StaleLinksTransformer({})

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "target.qmd"

            current_file.write_text("content")
            target_file.write_text("content")

            resolved = transformer._resolve_link_path("target.qmd", current_file, [])
            assert resolved == target_file.resolve()

    def test_resolve_link_path_nonexistent(self):
        """Test resolving link paths to non-existent files."""
        transformer = StaleLinksTransformer({})

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            current_file.write_text("content")

            resolved = transformer._resolve_link_path(
                "nonexistent.qmd", current_file, []
            )
            assert resolved is None

    def test_transform_preserve_image_links(self):
        """Test that image links are preserved and not treated as stale links."""
        content = """# Test Document

This is a [broken link](nonexistent.md) that should be removed.
This is an ![image link](./images/test.png) that should be preserved.
This is another [valid link](valid.qmd) that should be kept.

More content with ![another image](assets/photo.jpg).
"""

        expected_content = """# Test Document

This is a  that should be removed.
This is an ![image link](./images/test.png) that should be preserved.
This is another [valid link](valid.qmd) that should be kept.

More content with ![another image](assets/photo.jpg).
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.qmd"
            test_file.write_text(content)

            # Create a valid target file
            valid_file = temp_path / "valid.qmd"
            valid_file.write_text("# Valid content")

            emitted_files = [valid_file]

            transformer = StaleLinksTransformer({"remove_stale_links": True})
            transformer.transform(test_file, emitted_files)

            result_content = test_file.read_text()
            assert result_content.strip() == expected_content.strip()

    def test_transform_update_link_extensions(self):
        """Test that links to .md files are updated to .qmd when corresponding .qmd files are emitted."""
        content = """# Test Document

This is a [link to index](index.md) that should be updated to .qmd.
This is a [link to another page](another-page.md) that should also be updated.
This is a [broken link](nonexistent.md) that should be removed.
"""

        expected_content = """# Test Document

This is a [link to index](index.qmd) that should be updated to .qmd.
This is a [link to another page](another-page.qmd) that should also be updated.
This is a  that should be removed.
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.qmd"
            test_file.write_text(content)

            # Create emitted QMD files (simulating what QmdEmitter would produce)
            index_qmd = temp_path / "index.qmd"
            another_qmd = temp_path / "another-page.qmd"
            index_qmd.write_text("# Index content")
            another_qmd.write_text("# Another page content")

            emitted_files = [index_qmd, another_qmd]

            transformer = StaleLinksTransformer({"remove_stale_links": True})

            # Debug: Let's see what _resolve_link_path returns
            test_target = transformer._resolve_link_path(
                "index.md", test_file, emitted_files
            )
            print(f"Resolved 'index.md': {test_target}")

            # Debug: Let's see what _is_emitted_file returns
            if test_target:
                is_emitted = transformer._is_emitted_file(test_target, emitted_files)
                print(f"Is emitted: {is_emitted}")

                # Debug: Let's see what _get_updated_link_path returns
                updated_path = transformer._get_updated_link_path(
                    "index.md", test_target, emitted_files
                )
                print(f"Updated path: {updated_path}")

            transformer.transform(test_file, emitted_files)

            result_content = test_file.read_text()
            print("Expected:")
            print(repr(expected_content.strip()))
            print("Actual:")
            print(repr(result_content.strip()))
            assert result_content.strip() == expected_content.strip()

    def test_transform_links_with_spaces(self):
        """Test that links with spaces are properly handled and URL-encoded."""
        content = """# Test Document

This is a [link with spaces](fourth page.md) that should be updated.
This is a [broken link](nonexistent page.md) that should be removed.
"""

        expected_content = """# Test Document

This is a [link with spaces](fourth%20page.qmd) that should be updated.
This is a  that should be removed.
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.qmd"
            test_file.write_text(content)

            # Create emitted QMD file with space in name
            target_qmd = temp_path / "fourth page.qmd"
            target_qmd.write_text("# Fourth page content")

            emitted_files = [target_qmd]

            transformer = StaleLinksTransformer({"remove_stale_links": True})
            transformer.transform(test_file, emitted_files)

            result_content = test_file.read_text()
            assert result_content.strip() == expected_content.strip()

    def test_transform_already_encoded_links_with_spaces(self):
        """Test that already URL-encoded links with spaces are handled correctly."""
        content = """# Test Document

This is a [link with spaces](fourth%20page.md) that should be updated.
This is a [broken link](nonexistent%20page.md) that should be removed.
"""

        expected_content = """# Test Document

This is a [link with spaces](fourth%20page.qmd) that should be updated.
This is a  that should be removed.
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test.qmd"
            test_file.write_text(content)

            # Create emitted QMD file with space in name
            target_qmd = temp_path / "fourth page.qmd"
            target_qmd.write_text("# Fourth page content")

            emitted_files = [target_qmd]

            transformer = StaleLinksTransformer({"remove_stale_links": True})
            transformer.transform(test_file, emitted_files)

            result_content = test_file.read_text()
            assert result_content.strip() == expected_content.strip()

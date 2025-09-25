"""Test wikilink transformer functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.wikilink_transformer import WikilinkTransformer


class TestWikilinkTransformer:
    def test_init(self):
        """Test wikilink transformer initialization."""
        config = {"preserve_aliases": False, "link_extension": ".md"}
        transformer = WikilinkTransformer(config)

        assert transformer.preserve_aliases is False
        assert transformer.link_extension == ".md"

    def test_init_defaults(self):
        """Test wikilink transformer initialization with defaults."""
        transformer = WikilinkTransformer({})

        assert transformer.preserve_aliases is True
        assert transformer.link_extension == ".qmd"

    def test_find_target_file_exact_match(self):
        """Test finding target file with exact stem match."""
        transformer = WikilinkTransformer({})

        with TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "target.qmd"
            file2 = Path(temp_dir) / "other.qmd"
            current_file = Path(temp_dir) / "current.qmd"

            emitted_files = [file1, file2, current_file]

            found = transformer._find_target_file("target", emitted_files, current_file)
            assert found == file1

    def test_find_target_file_with_extension(self):
        """Test finding target file with extension."""
        transformer = WikilinkTransformer({})

        with TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "target.qmd"
            current_file = Path(temp_dir) / "current.qmd"

            emitted_files = [file1, current_file]

            found = transformer._find_target_file(
                "target.qmd", emitted_files, current_file
            )
            assert found == file1

    def test_find_target_file_case_insensitive(self):
        """Test finding target file with case insensitive match."""
        transformer = WikilinkTransformer({})

        with TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "Target.qmd"
            current_file = Path(temp_dir) / "current.qmd"

            emitted_files = [file1, current_file]

            found = transformer._find_target_file("target", emitted_files, current_file)
            assert found == file1

    def test_find_target_file_not_found(self):
        """Test finding target file when it doesn't exist."""
        transformer = WikilinkTransformer({})

        with TemporaryDirectory() as temp_dir:
            file1 = Path(temp_dir) / "other.qmd"
            current_file = Path(temp_dir) / "current.qmd"

            emitted_files = [file1, current_file]

            found = transformer._find_target_file(
                "nonexistent", emitted_files, current_file
            )
            assert found is None

    def test_get_relative_path_same_dir(self):
        """Test getting relative path for files in same directory."""
        transformer = WikilinkTransformer({})

        from_file = Path("/project/docs/current.qmd")
        to_file = Path("/project/docs/target.qmd")

        relative_path = transformer._get_relative_path(from_file, to_file)
        assert relative_path == "target.qmd"

    def test_get_relative_path_subdirectory(self):
        """Test getting relative path for file in subdirectory."""
        transformer = WikilinkTransformer({})

        from_file = Path("/project/current.qmd")
        to_file = Path("/project/docs/target.qmd")

        relative_path = transformer._get_relative_path(from_file, to_file)
        assert relative_path == "docs/target.qmd"

    def test_get_relative_path_parent_directory(self):
        """Test getting relative path for file in parent directory."""
        transformer = WikilinkTransformer({})

        from_file = Path("/project/docs/current.qmd")
        to_file = Path("/project/target.qmd")

        relative_path = transformer._get_relative_path(from_file, to_file)
        assert relative_path == "../target.qmd"

    def test_transform_simple_wikilink(self):
        """Test transforming simple wikilinks."""
        content = """# Test Document

This links to [[target-page]].
"""

        expected = """# Test Document

This links to [target-page](target.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "target.qmd"

            current_file.write_text(content)
            emitted_files = [current_file, target_file]

            transformer = WikilinkTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_wikilink_with_alias(self):
        """Test transforming wikilinks with aliases."""
        content = """# Test Document

This links to [[target-page|Custom Title]].
"""

        expected = """# Test Document

This links to [Custom Title](target.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "target.qmd"

            current_file.write_text(content)
            emitted_files = [current_file, target_file]

            transformer = WikilinkTransformer({"preserve_aliases": True})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_wikilink_ignore_alias(self):
        """Test transforming wikilinks ignoring aliases."""
        content = """# Test Document

This links to [[target-page|Custom Title]].
"""

        expected = """# Test Document

This links to [target-page](target.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "target.qmd"

            current_file.write_text(content)
            emitted_files = [current_file, target_file]

            transformer = WikilinkTransformer({"preserve_aliases": False})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_broken_wikilink(self):
        """Test transforming wikilinks to non-existent files."""
        content = """# Test Document

This links to [[nonexistent-page]].
"""

        expected = """# Test Document

This links to nonexistent-page.
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = WikilinkTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_broken_wikilink_with_alias(self):
        """Test transforming wikilinks with aliases to non-existent files."""
        content = """# Test Document

This links to [[nonexistent-page|Custom Title]].
"""

        expected = """# Test Document

This links to Custom Title.
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"

            current_file.write_text(content)
            emitted_files = [current_file]

            transformer = WikilinkTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_wikilink_with_spaces(self):
        """Test transforming wikilinks with spaces in filename."""
        content = """# Test Document

This links to [[fourth page]].
"""

        expected = """# Test Document

This links to [fourth page](fourth%20page.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "fourth page.qmd"

            current_file.write_text(content)
            target_file.write_text("# Fourth Page")
            emitted_files = [current_file, target_file]

            transformer = WikilinkTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_transform_wikilink_with_spaces_and_alias(self):
        """Test transforming wikilinks with spaces and aliases."""
        content = """# Test Document

This links to [[fourth page|Custom Title]].
"""

        expected = """# Test Document

This links to [Custom Title](fourth%20page.qmd).
"""

        with TemporaryDirectory() as temp_dir:
            current_file = Path(temp_dir) / "current.qmd"
            target_file = Path(temp_dir) / "fourth page.qmd"

            current_file.write_text(content)
            target_file.write_text("# Fourth Page")
            emitted_files = [current_file, target_file]

            transformer = WikilinkTransformer({})
            transformer.transform(current_file, emitted_files)

            result = current_file.read_text()
            assert result == expected

    def test_get_relative_path_with_spaces(self):
        """Test getting relative path for files with spaces."""
        transformer = WikilinkTransformer({})

        from_file = Path("/project/current.qmd")
        to_file = Path("/project/fourth page.qmd")

        relative_path = transformer._get_relative_path(from_file, to_file)
        assert relative_path == "fourth%20page.qmd"

    def test_transform_wikilink_image_syntax(self):
        """Test transforming wikilink image syntax ![[image.png]] to ![](./path/image.png)."""
        content = """# Test Document

Regular wikilink image:
![[test_image.png]]

Wikilink image with path:
![[images/nested_image.jpg]]

Wikilink image with spaces:
![[image with spaces.png]]
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "test.qmd"
            source_file.write_text(content)

            # Create target images
            (temp_path / "test_image.png").write_text("fake png")

            images_dir = temp_path / "images"
            images_dir.mkdir()
            (images_dir / "nested_image.jpg").write_text("fake jpg")

            (temp_path / "image with spaces.png").write_text("fake png with spaces")

            # Simulate emitted files list
            emitted_files = [
                temp_path / "test_image.png",
                images_dir / "nested_image.jpg",
                temp_path / "image with spaces.png",
            ]

            transformer = WikilinkTransformer({})
            transformer.transform(source_file, emitted_files)

            transformed_content = source_file.read_text()

            # Check that wikilink images were converted to proper markdown syntax
            assert "![](./test_image.png)" in transformed_content
            assert "![](./images/nested_image.jpg)" in transformed_content
            assert "![](./image%20with%20spaces.png)" in transformed_content

            # Ensure original wikilink syntax is gone
            assert "![[" not in transformed_content

    def test_transform_wikilink_image_with_url_encoding(self):
        """Test transforming URL-encoded wikilink images like ![[image%20with%20spaces.png]]."""
        content = """# Test Document

URL-encoded wikilink image:
![[image%20with%20spaces.png]]

URL-encoded nested path:
![[images%2Fnested%20image.jpg]]
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "test.qmd"
            source_file.write_text(content)

            # Create target images (with actual spaces in filenames)
            (temp_path / "image with spaces.png").write_text("fake png with spaces")

            images_dir = temp_path / "images"
            images_dir.mkdir()
            (images_dir / "nested image.jpg").write_text("fake nested jpg")

            # Simulate emitted files list
            emitted_files = [
                temp_path / "image with spaces.png",
                images_dir / "nested image.jpg",
            ]

            transformer = WikilinkTransformer({})
            transformer.transform(source_file, emitted_files)

            transformed_content = source_file.read_text()

            # Check that URL-encoded wikilinks were decoded and matched correctly
            assert "![](./image%20with%20spaces.png)" in transformed_content
            assert "![](./images/nested%20image.jpg)" in transformed_content

            # Ensure original wikilink syntax is gone
            assert "![[" not in transformed_content

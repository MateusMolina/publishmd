"""Test assets emitter functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.emitters.assets_emitter import AssetsEmitter


class TestAssetsEmitter:
    def test_init(self):
        """Test assets emitter initialization."""
        config = {"asset_extensions": [".png", ".jpg"], "file_extensions": [".md"]}
        emitter = AssetsEmitter(config)

        assert emitter.asset_extensions == [".png", ".jpg"]
        assert emitter.file_extensions == [".md"]

    def test_init_defaults(self):
        """Test assets emitter initialization with defaults."""
        emitter = AssetsEmitter({})

        assert ".png" in emitter.asset_extensions
        assert ".jpg" in emitter.asset_extensions
        assert emitter.file_extensions == [".md", ".markdown", ".qmd"]

    def test_is_url(self):
        """Test URL detection."""
        emitter = AssetsEmitter({})

        assert emitter._is_url("https://example.com/image.png") is True
        assert emitter._is_url("http://example.com/image.png") is True
        assert emitter._is_url("ftp://example.com/file.txt") is True
        assert emitter._is_url("./local/image.png") is False
        assert emitter._is_url("/absolute/path.png") is False
        assert emitter._is_url("relative.png") is False

    def test_is_asset_file(self):
        """Test asset file detection."""
        emitter = AssetsEmitter({})

        assert emitter._is_asset_file(Path("image.png")) is True
        assert emitter._is_asset_file(Path("image.JPG")) is True  # Case insensitive
        assert emitter._is_asset_file(Path("document.txt")) is False

    def test_extract_assets_markdown_images(self):
        """Test extracting assets from markdown image syntax."""
        content = """# Test Document

![Alt text](./images/test.png)
![Another image](../assets/photo.jpg)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir)

            # Create test structure
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "test.png").write_text("fake image")

            assets_dir = input_dir / "assets"
            assets_dir.mkdir()
            (assets_dir / "photo.jpg").write_text("fake photo")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            assets = emitter._extract_assets_from_file(md_file, input_dir)

            assert len(assets) == 2
            asset_names = {asset.name for asset in assets}
            assert "test.png" in asset_names
            assert "photo.jpg" in asset_names

    def test_extract_assets_markdown_links(self):
        """Test extracting assets from markdown link syntax."""
        content = """# Test Document

Download the [PDF file](./documents/manual.pdf).
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir)

            # Create test structure
            docs_dir = input_dir / "documents"
            docs_dir.mkdir()
            (docs_dir / "manual.pdf").write_text("fake pdf")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            assets = emitter._extract_assets_from_file(md_file, input_dir)

            assert len(assets) == 1
            assert assets.pop().name == "manual.pdf"

    def test_extract_assets_html_images(self):
        """Test extracting assets from HTML img tags."""
        content = """# Test Document

<img src="./images/test.png" alt="Test image">
<img src='../assets/photo.jpg' alt='Photo'>
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir)

            # Create test structure
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "test.png").write_text("fake image")

            assets_dir = input_dir / "assets"
            assets_dir.mkdir()
            (assets_dir / "photo.jpg").write_text("fake photo")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            assets = emitter._extract_assets_from_file(md_file, input_dir)

            assert len(assets) == 2
            asset_names = {asset.name for asset in assets}
            assert "test.png" in asset_names
            assert "photo.jpg" in asset_names

    def test_extract_assets_skip_urls(self):
        """Test that URLs are skipped when extracting assets."""
        content = """# Test Document

![Remote image](https://example.com/image.png)
![Local image](./local.png)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir)

            # Create local image
            (input_dir / "local.png").write_text("fake image")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            assets = emitter._extract_assets_from_file(md_file, input_dir)

            # Only local image should be found
            assert len(assets) == 1
            assert assets.pop().name == "local.png"

    def test_emit_assets(self):
        """Test emitting assets to output directory."""
        content = """# Test Document

![Image](./images/test.png)
[PDF](./docs/manual.pdf)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create test assets
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "test.png").write_text("fake png content")

            docs_dir = input_dir / "docs"
            docs_dir.mkdir()
            (docs_dir / "manual.pdf").write_text("fake pdf content")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            emitted_files = emitter.emit([md_file], output_dir)  # New API

            assert len(emitted_files) == 2

            # Check that files were copied correctly
            output_image = output_dir / "images" / "test.png"
            output_pdf = output_dir / "docs" / "manual.pdf"

            assert output_image.exists()
            assert output_pdf.exists()

    def test_emit_assets_with_filtered_list(self):
        """Test emitting assets only from files provided in filtered list."""
        # File that should be included (publish: true)
        included_content = """---
title: Published Document
publish: true
---

![Image](./images/published.png)
[PDF](./docs/published.pdf)
"""

        # File that should be excluded (publish: false)
        excluded_content = """---
title: Draft Document
publish: false
---

![Image](./images/draft.png)
[PDF](./docs/draft.pdf)
"""

        # File with no frontmatter (should be excluded when filter is set)
        no_frontmatter_content = """# No Frontmatter Document

![Image](./images/no_frontmatter.png)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create test assets
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "published.png").write_text("published image")
            (images_dir / "draft.png").write_text("draft image")
            (images_dir / "no_frontmatter.png").write_text("no frontmatter image")

            docs_dir = input_dir / "docs"
            docs_dir.mkdir()
            (docs_dir / "published.pdf").write_text("published pdf")
            (docs_dir / "draft.pdf").write_text("draft pdf")

            # Create markdown files
            published_file = input_dir / "published.md"
            draft_file = input_dir / "draft.md"
            no_frontmatter_file = input_dir / "no_frontmatter.md"

            published_file.write_text(included_content)
            draft_file.write_text(excluded_content)
            no_frontmatter_file.write_text(no_frontmatter_content)

            # Simulate filtering by only providing the published file
            filtered_files = [published_file]  # Changed from set to list

            emitter = AssetsEmitter({})
            emitted_files = emitter.emit(filtered_files, output_dir)  # New API

            # Should only emit assets from the published file
            assert len(emitted_files) == 2

            # Check that only published assets were copied
            output_image = output_dir / "images" / "published.png"
            output_pdf = output_dir / "docs" / "published.pdf"

            assert output_image.exists()
            assert output_pdf.exists()
            assert output_image.read_text() == "published image"
            assert output_pdf.read_text() == "published pdf"

            # Check that draft and no-frontmatter assets were NOT copied
            draft_image = output_dir / "images" / "draft.png"
            draft_pdf = output_dir / "docs" / "draft.pdf"
            no_frontmatter_image = output_dir / "images" / "no_frontmatter.png"

            assert not draft_image.exists()
            assert not draft_pdf.exists()
            assert not no_frontmatter_image.exists()

    def test_emit_assets_no_frontmatter_filter(self):
        """Test that assets from provided files are emitted."""
        # This tests the new behavior - only process assets from provided files
        content = """![Image](./images/test.png)"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create test assets
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "test.png").write_text("test image")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            # Configure emitter without frontmatter filter
            config = {}
            emitter = AssetsEmitter(config)
            emitted_files = emitter.emit([md_file], output_dir)  # New API

            assert len(emitted_files) == 1
            output_image = output_dir / "images" / "test.png"
            assert output_image.exists()

    def test_extract_assets_with_spaces_in_filenames(self):
        """Test extracting assets with spaces in filenames."""
        content = """# Test Document

![Image with space](./images/my image.png)
![URL encoded image](./images/my%20image.png)
[PDF with space](./docs/my document.pdf)
[URL encoded PDF](./docs/my%20document.pdf)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create test assets with spaces in names
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "my image.png").write_text("fake image with space")

            docs_dir = input_dir / "docs"
            docs_dir.mkdir()
            (docs_dir / "my document.pdf").write_text("fake pdf with space")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            emitted_files = emitter.emit([md_file], output_dir)

            # Should find both the regular space and URL-encoded references to the same files
            assert len(emitted_files) == 2

            # Check that files were copied correctly
            output_image = output_dir / "images" / "my image.png"
            output_pdf = output_dir / "docs" / "my document.pdf"

            assert output_image.exists()
            assert output_pdf.exists()
            assert output_image.read_text() == "fake image with space"
            assert output_pdf.read_text() == "fake pdf with space"

    def test_extract_assets_nested_paths_with_spaces(self):
        """Test extracting assets from nested directories with spaces."""
        content = """# Test Document

![Nested image](./folder with spaces/image.png)
[Nested asset](./folder%20with%20spaces/document.pdf)
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create nested directory with spaces
            nested_dir = input_dir / "folder with spaces"
            nested_dir.mkdir()
            (nested_dir / "image.png").write_text("nested image")
            (nested_dir / "document.pdf").write_text("nested document")

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            emitted_files = emitter.emit([md_file], output_dir)

            # Should find both references to files in the directory with spaces
            assert len(emitted_files) == 2

            # Check that files were copied with correct directory structure
            output_image = output_dir / "folder with spaces" / "image.png"
            output_pdf = output_dir / "folder with spaces" / "document.pdf"

            assert output_image.exists()
            assert output_pdf.exists()

    def test_extract_assets_wikilink_style(self):
        """Test extracting assets from wikilink-style references."""
        content = """# Test Document

![[image with space.png]]
[[document with space.pdf]]
![[folder with spaces/nested image.jpg]]
[[folder%20with%20spaces/encoded%20document.pdf]]
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()

            # Create test assets with spaces in names
            (input_dir / "image with space.png").write_text("wikilink image with space")
            (input_dir / "document with space.pdf").write_text(
                "wikilink pdf with space"
            )

            # Create nested directory with spaces
            nested_dir = input_dir / "folder with spaces"
            nested_dir.mkdir()
            (nested_dir / "nested image.jpg").write_text("nested wikilink image")
            (nested_dir / "encoded document.pdf").write_text(
                "encoded wikilink document"
            )

            # Create markdown file
            md_file = input_dir / "test.md"
            md_file.write_text(content)

            emitter = AssetsEmitter({})
            emitted_files = emitter.emit([md_file], output_dir)

            # Should find all 4 wikilink references
            assert len(emitted_files) == 4

            # Check that files were copied correctly
            output_image = output_dir / "image with space.png"
            output_pdf = output_dir / "document with space.pdf"
            output_nested_image = output_dir / "folder with spaces" / "nested image.jpg"
            output_encoded_pdf = (
                output_dir / "folder with spaces" / "encoded document.pdf"
            )

            assert output_image.exists()
            assert output_pdf.exists()
            assert output_nested_image.exists()
            assert output_encoded_pdf.exists()

            assert output_image.read_text() == "wikilink image with space"
            assert output_pdf.read_text() == "wikilink pdf with space"
            assert output_nested_image.read_text() == "nested wikilink image"
            assert output_encoded_pdf.read_text() == "encoded wikilink document"

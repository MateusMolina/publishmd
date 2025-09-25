"""Test frontmatter filter functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.filters import FrontmatterFilter


class TestFrontmatterFilter:
    def test_init_empty(self):
        """Test filter initialization with no config."""
        filter_obj = FrontmatterFilter({})
        assert filter_obj.config == {}

    def test_init_with_config(self):
        """Test filter initialization with config."""
        config = {"publish": True, "status": "draft"}
        filter_obj = FrontmatterFilter(config)
        assert filter_obj.config == config

    def test_should_include_no_filter(self):
        """Test that files are included when no filter is configured."""
        filter_obj = FrontmatterFilter({})

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text("# Test\nSome content")

            assert filter_obj.should_include(file_path) is True

    def test_should_include_with_matching_frontmatter(self):
        """Test that files are included when frontmatter matches filter."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        content = """---
title: Test Document
publish: true
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is True

    def test_should_exclude_with_non_matching_frontmatter(self):
        """Test that files are excluded when frontmatter doesn't match filter."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        content = """---
title: Test Document
publish: false
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is False

    def test_should_exclude_with_missing_frontmatter_key(self):
        """Test that files are excluded when frontmatter is missing required key."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        content = """---
title: Test Document
draft: false
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is False

    def test_should_exclude_with_no_frontmatter(self):
        """Test that files are excluded when they have no frontmatter but filter is configured."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        content = """# Test
Some content without frontmatter"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is False

    def test_should_include_with_multiple_criteria(self):
        """Test that files are included when all frontmatter criteria match."""
        filter_config = {"publish": True, "status": "ready"}
        filter_obj = FrontmatterFilter(filter_config)

        content = """---
title: Test Document
publish: true
status: ready
author: John Doe
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is True

    def test_should_exclude_with_partial_criteria_match(self):
        """Test that files are excluded when only some frontmatter criteria match."""
        filter_config = {"publish": True, "status": "ready"}
        filter_obj = FrontmatterFilter(filter_config)

        content = """---
title: Test Document
publish: true
status: draft
author: John Doe
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert filter_obj.should_include(file_path) is False

    def test_extract_frontmatter_valid_yaml(self):
        """Test extracting valid YAML frontmatter."""
        filter_obj = FrontmatterFilter({})

        content = """---
title: Test Document
publish: true
tags:
  - test
  - markdown
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            frontmatter = filter_obj._extract_frontmatter(file_path)

            assert frontmatter is not None
            assert frontmatter["title"] == "Test Document"
            assert frontmatter["publish"] is True
            assert frontmatter["tags"] == ["test", "markdown"]

    def test_extract_frontmatter_no_frontmatter(self):
        """Test extracting frontmatter from file without frontmatter."""
        filter_obj = FrontmatterFilter({})

        content = """# Test
Some content without frontmatter"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            frontmatter = filter_obj._extract_frontmatter(file_path)
            assert frontmatter is None

    def test_extract_frontmatter_invalid_yaml(self):
        """Test extracting invalid YAML frontmatter."""
        filter_obj = FrontmatterFilter({})

        content = """---
title: Test Document
publish: true
invalid: [unclosed list
---

# Test
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            frontmatter = filter_obj._extract_frontmatter(file_path)
            assert frontmatter is None

    def test_extract_frontmatter_malformed_delimiter(self):
        """Test extracting frontmatter with malformed delimiter."""
        filter_obj = FrontmatterFilter({})

        content = """---
title: Test Document
publish: true

# Test (missing closing ---)
Some content"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            frontmatter = filter_obj._extract_frontmatter(file_path)
            assert frontmatter is None

    def test_should_exclude_non_markdown_files(self):
        """Test that non-markdown files are excluded even with no filter config."""
        filter_obj = FrontmatterFilter({})

        with TemporaryDirectory() as temp_dir:
            # Test various non-markdown file types
            txt_file = Path(temp_dir) / "test.txt"
            py_file = Path(temp_dir) / "test.py"
            json_file = Path(temp_dir) / "test.json"

            txt_file.write_text("Some text content")
            py_file.write_text("print('hello')")
            json_file.write_text('{"key": "value"}')

            # All should be excluded because they're not markdown files
            assert filter_obj.should_include(txt_file) is False
            assert filter_obj.should_include(py_file) is False
            assert filter_obj.should_include(json_file) is False

    def test_should_exclude_non_markdown_files_with_filter(self):
        """Test that non-markdown files are excluded even when filter is configured."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        with TemporaryDirectory() as temp_dir:
            # Test various non-markdown file types
            txt_file = Path(temp_dir) / "test.txt"
            py_file = Path(temp_dir) / "test.py"

            txt_file.write_text("Some text content")
            py_file.write_text("print('hello')")

            # All should be excluded because they're not markdown files
            assert filter_obj.should_include(txt_file) is False
            assert filter_obj.should_include(py_file) is False

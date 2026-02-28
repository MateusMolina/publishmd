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
        """Test that files are kept when no filter is configured."""
        filter_obj = FrontmatterFilter({})

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text("# Test\nSome content")

            assert file_path in filter_obj.filter([file_path])

    def test_should_include_with_matching_frontmatter(self):
        """Test that files are kept when frontmatter matches filter."""
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

            assert file_path in filter_obj.filter([file_path])

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

            assert file_path not in filter_obj.filter([file_path])

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

            assert file_path not in filter_obj.filter([file_path])

    def test_should_exclude_with_no_frontmatter(self):
        """Test that files are excluded when they have no frontmatter but filter is configured."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        content = """# Test
Some content without frontmatter"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            assert file_path not in filter_obj.filter([file_path])

    def test_should_include_with_multiple_criteria(self):
        """Test that files are kept when all frontmatter criteria match."""
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

            assert file_path in filter_obj.filter([file_path])

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

            assert file_path not in filter_obj.filter([file_path])

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

    def test_should_pass_through_non_markdown_files(self):
        """Non-markdown files pass through FrontmatterFilter (it only screens markdown)."""
        filter_obj = FrontmatterFilter({})

        with TemporaryDirectory() as temp_dir:
            txt_file = Path(temp_dir) / "test.txt"
            py_file = Path(temp_dir) / "test.py"
            json_file = Path(temp_dir) / "test.json"

            txt_file.write_text("Some text content")
            py_file.write_text("print('hello')")
            json_file.write_text('{"key": "value"}')

            # Non-markdown files pass through - FrontmatterFilter targets only .md/.qmd
            result = filter_obj.filter([txt_file, py_file, json_file])
            assert txt_file in result
            assert py_file in result
            assert json_file in result

    def test_should_pass_through_non_markdown_files_with_filter(self):
        """Non-markdown files pass through even when a frontmatter filter is configured."""
        filter_config = {"publish": True}
        filter_obj = FrontmatterFilter(filter_config)

        with TemporaryDirectory() as temp_dir:
            txt_file = Path(temp_dir) / "test.txt"
            py_file = Path(temp_dir) / "test.py"

            txt_file.write_text("Some text content")
            py_file.write_text("print('hello')")

            # Non-markdown files pass through unconditionally
            result = filter_obj.filter([txt_file, py_file])
            assert txt_file in result
            assert py_file in result

    def test_filter_keeps_matching_md_files(self):
        filter_obj = FrontmatterFilter({"publish": True})
        content_yes = "---\npublish: true\n---\n# Hi"
        content_no = "---\npublish: false\n---\n# Hi"
        with TemporaryDirectory() as tmp:
            yes = Path(tmp) / "yes.md"
            no = Path(tmp) / "no.md"
            yes.write_text(content_yes)
            no.write_text(content_no)
            result = filter_obj.filter([yes, no])
            assert yes in result
            assert no not in result

    def test_filter_passes_non_markdown_through(self):
        filter_obj = FrontmatterFilter({"publish": True})
        with TemporaryDirectory() as tmp:
            png = Path(tmp) / "pic.png"
            md = Path(tmp) / "doc.md"
            png.write_bytes(b"")
            md.write_text("---\npublish: false\n---")
            result = filter_obj.filter([png, md])
            assert png in result
            assert md not in result

    def test_filter_empty_list(self):
        filter_obj = FrontmatterFilter({})
        assert filter_obj.filter([]) == []


# ---------------------------------------------------------------------------
# IgnoreFolderFilter tests
# ---------------------------------------------------------------------------

from publishmd.filters import IgnoreFolderFilter  # noqa: E402


class TestIgnoreFolderFilter:
    def test_filter_excludes_ignored_folder(self):
        with TemporaryDirectory() as tmp:
            drafts = Path(tmp) / "drafts"
            posts = Path(tmp) / "posts"
            drafts.mkdir()
            posts.mkdir()
            a = drafts / "a.md"
            b = posts / "b.md"
            a.write_text("")
            b.write_text("")
            f = IgnoreFolderFilter({"ignored_folders": ["drafts"]})
            result = f.filter([a, b])
            assert a not in result
            assert b in result

    def test_filter_empty_list(self):
        f = IgnoreFolderFilter({"ignored_folders": []})
        assert f.filter([]) == []

    def test_filter_no_ignored_keeps_all(self):
        with TemporaryDirectory() as tmp:
            files = [Path(tmp) / "a.md", Path(tmp) / "b.md"]
            f = IgnoreFolderFilter({"ignored_folders": []})
            assert f.filter(files) == files


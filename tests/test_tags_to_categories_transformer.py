"""Test tags to categories transformer functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.tags_to_categories_transformer import TagsToCategoriesTransformer


class TestTagsToCategoriesTransformer:
    def test_init(self):
        """Test tags to categories transformer initialization."""
        config = {}
        transformer = TagsToCategoriesTransformer(config)
        assert transformer.config == config

    def test_transform_no_frontmatter(self):
        """Test transforming file without frontmatter."""
        content = """# Test Document

This is a test document without frontmatter.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == content

    def test_transform_no_tags(self):
        """Test transforming file with frontmatter but no tags."""
        content = """---
title: "Test Document"
author: "Test Author"
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == content

    def test_transform_tags_to_categories_new(self):
        """Test converting tags to categories when categories doesn't exist."""
        content = """---
title: "Test Document"
tags: ["tag1", "tag2"]
---

# Test Document

This is a test document.
"""

        expected = """---
categories:
- tag1
- tag2
title: Test Document
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == expected

    def test_transform_tags_to_categories_merge(self):
        """Test merging tags into existing categories."""
        content = """---
title: "Test Document"
categories: ["existing1", "existing2"]
tags: ["tag1", "tag2"]
---

# Test Document

This is a test document.
"""

        expected = """---
categories:
- existing1
- existing2
- tag1
- tag2
title: Test Document
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == expected

    def test_transform_tags_to_categories_merge_with_duplicates(self):
        """Test merging tags into existing categories with duplicates."""
        content = """---
title: "Test Document"
categories: ["tag1", "existing2"]
tags: ["tag1", "tag2"]
---

# Test Document

This is a test document.
"""

        expected = """---
categories:
- tag1
- existing2
- tag2
title: Test Document
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == expected

    def test_transform_single_tag_string(self):
        """Test converting single tag string to categories."""
        content = """---
title: "Test Document"
tags: "single-tag"
---

# Test Document

This is a test document.
"""

        expected = """---
categories:
- single-tag
title: Test Document
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == expected

    def test_transform_single_category_string_merge(self):
        """Test merging single tag string into single category string."""
        content = """---
title: "Test Document"
categories: "existing-category"
tags: "new-tag"
---

# Test Document

This is a test document.
"""

        expected = """---
categories:
- existing-category
- new-tag
title: Test Document
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == expected

    def test_transform_invalid_frontmatter(self):
        """Test transforming file with invalid frontmatter."""
        content = """---
title: "Test Document"
tags: ["tag1"
---

# Test Document

This is a test document.
"""

        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.md"
            file_path.write_text(content)

            transformer = TagsToCategoriesTransformer({})
            transformer.transform(file_path, [])

            result = file_path.read_text()
            assert result == content  # Should remain unchanged

    def test_transform_nonexistent_file(self):
        """Test transforming nonexistent file."""
        transformer = TagsToCategoriesTransformer({})

        nonexistent_file = Path("/nonexistent/file.md")
        transformer.transform(nonexistent_file, [])

        # Should not raise an exception
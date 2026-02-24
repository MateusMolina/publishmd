"""Tests for RenameFrontmatterFieldTransformer."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.rename_frontmatter_field_transformer import (
    RenameFrontmatterFieldTransformer,
)


class TestRenameFrontmatterFieldTransformer:
    """Unit tests for RenameFrontmatterFieldTransformer."""

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def test_init_required_fields(self):
        """Constructor stores from_field and to_field."""
        t = RenameFrontmatterFieldTransformer(
            {"from_field": "modified", "to_field": "date-modified"}
        )
        assert t.from_field == "modified"
        assert t.to_field == "date-modified"
        assert t.overwrite is False

    def test_init_overwrite_flag(self):
        """overwrite option is stored correctly."""
        t = RenameFrontmatterFieldTransformer(
            {"from_field": "a", "to_field": "b", "overwrite": True}
        )
        assert t.overwrite is True

    def test_init_missing_required_raises(self):
        """Missing from_field or to_field raises KeyError."""
        with pytest.raises(KeyError):
            RenameFrontmatterFieldTransformer({"to_field": "b"})
        with pytest.raises(KeyError):
            RenameFrontmatterFieldTransformer({"from_field": "a"})

    # ------------------------------------------------------------------
    # Core rename behaviour
    # ------------------------------------------------------------------

    def test_renames_field(self):
        """from_field is renamed to to_field in the frontmatter."""
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(
                "---\ntitle: Test\nmodified: 2026-01-10\n---\n\nBody.\n",
                encoding="utf-8",
            )

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "modified", "to_field": "date-modified"}
            )
            t.transform(f, [])

            content = f.read_text(encoding="utf-8")
            assert "date-modified:" in content
            # 'modified:' alone (not as a suffix of date-modified) should be gone
            fm_block = content.split("---")[1]
            assert "date-modified:" in fm_block
            assert "\nmodified:" not in fm_block
            assert "Body." in content

    def test_field_not_present_is_noop(self):
        """When from_field is absent the file is left untouched."""
        original = "---\ntitle: Test\n---\n\nBody.\n"
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(original, encoding="utf-8")

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "modified", "to_field": "date-modified"}
            )
            t.transform(f, [])

            assert f.read_text(encoding="utf-8") == original

    def test_no_frontmatter_is_noop(self):
        """Files without frontmatter are left untouched."""
        original = "# Title\n\nJust text.\n"
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(original, encoding="utf-8")

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "modified", "to_field": "date-modified"}
            )
            t.transform(f, [])

            assert f.read_text(encoding="utf-8") == original

    def test_preserves_field_value(self):
        """The renamed field carries the original value."""
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(
                "---\ncreated: 2025-11-01\n---\n\nBody.\n",
                encoding="utf-8",
            )

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "created", "to_field": "date"}
            )
            t.transform(f, [])

            content = f.read_text(encoding="utf-8")
            assert "date:" in content
            assert "2025-11-01" in content

    def test_preserves_body(self):
        """The file body below the frontmatter is not modified."""
        body = "\n# Hello\n\nThis is body content.\n"
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(f"---\nfoo: bar\n---\n{body}", encoding="utf-8")

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "foo", "to_field": "baz"}
            )
            t.transform(f, [])

            result = f.read_text(encoding="utf-8")
            assert result.endswith(body)

    # ------------------------------------------------------------------
    # to_field already exists
    # ------------------------------------------------------------------

    def test_skip_when_to_field_exists_by_default(self):
        """When to_field already exists and overwrite=False, nothing changes."""
        original = "---\ntitle: T\ndate: 2025-01-01\ncreated: 2024-06-01\n---\n\nBody.\n"
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(original, encoding="utf-8")

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "created", "to_field": "date"}
            )
            t.transform(f, [])

            # File should be unchanged because 'date' already exists
            assert f.read_text(encoding="utf-8") == original

    def test_overwrite_when_flag_set(self):
        """When overwrite=True and to_field exists, it is replaced by from_field's value."""
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(
                "---\ntitle: T\ndate: 2025-01-01\ncreated: 2024-06-01\n---\n\nBody.\n",
                encoding="utf-8",
            )

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "created", "to_field": "date", "overwrite": True}
            )
            t.transform(f, [])

            content = f.read_text(encoding="utf-8")
            assert "created:" not in content
            assert "2024-06-01" in content   # new value

    # ------------------------------------------------------------------
    # Multiple independent instances (pipeline behaviour)
    # ------------------------------------------------------------------

    def test_two_instances_in_sequence(self):
        """Two transformer instances applied in sequence each rename their own field."""
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "page.qmd"
            f.write_text(
                "---\ntitle: T\nmodified: 2026-01-10\ncreated: 2025-11-01\n---\n\nBody.\n",
                encoding="utf-8",
            )

            t1 = RenameFrontmatterFieldTransformer(
                {"from_field": "modified", "to_field": "date-modified"}
            )
            t2 = RenameFrontmatterFieldTransformer(
                {"from_field": "created", "to_field": "date"}
            )

            t1.transform(f, [])
            t2.transform(f, [])

            content = f.read_text(encoding="utf-8")
            fm_block = content.split("---\n", 2)[1]
            assert "date-modified:" in fm_block
            assert "date:" in fm_block
            assert "\nmodified:" not in fm_block
            assert "created:" not in fm_block
            assert "2026-01-10" in content
            assert "2025-11-01" in content

    def test_same_instance_applied_to_multiple_files(self):
        """A single instance transforms every file it is applied to."""
        with TemporaryDirectory() as tmp:
            files = []
            for i in range(3):
                f = Path(tmp) / f"page{i}.qmd"
                f.write_text(
                    f"---\ntitle: P{i}\nmodified: 2026-0{i+1}-01\n---\n\nBody {i}.\n",
                    encoding="utf-8",
                )
                files.append(f)

            t = RenameFrontmatterFieldTransformer(
                {"from_field": "modified", "to_field": "date-modified"}
            )
            for f in files:
                t.transform(f, files)

            for f in files:
                content = f.read_text(encoding="utf-8")
                fm_block = content.split("---\n", 2)[1]
                assert "date-modified:" in fm_block
                assert "\nmodified:" not in fm_block

"""Tests for ExtensionFilter."""

from pathlib import Path

import pytest

from publishmd.filters.extension_filter import ExtensionFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_filter(extensions: list) -> ExtensionFilter:
    return ExtensionFilter({"extensions": extensions})


# ---------------------------------------------------------------------------
# filter – per-file / single-item cases
# ---------------------------------------------------------------------------

class TestFilterSingleFile:
    def test_matching_extension_kept(self, tmp_path: Path):
        f = _make_filter([".md", ".qmd"])
        p = tmp_path / "post.md"
        assert p in f.filter([p])

    def test_non_matching_extension_dropped(self, tmp_path: Path):
        f = _make_filter([".md"])
        p = tmp_path / "image.png"
        assert p not in f.filter([p])

    def test_case_insensitive(self, tmp_path: Path):
        f = _make_filter([".md"])
        p = tmp_path / "POST.MD"
        assert p in f.filter([p])

    def test_empty_extensions_keeps_all(self, tmp_path: Path):
        f = _make_filter([])
        p = tmp_path / "anything.xyz"
        assert p in f.filter([p])

    def test_multiple_allowed_extensions(self, tmp_path: Path):
        f = _make_filter([".md", ".qmd", ".markdown"])
        assert (tmp_path / "report.qmd") in f.filter([tmp_path / "report.qmd"])
        assert (tmp_path / "notes.markdown") in f.filter([tmp_path / "notes.markdown"])
        assert (tmp_path / "diagram.svg") not in f.filter([tmp_path / "diagram.svg"])

    def test_extension_with_uppercase_config(self, tmp_path: Path):
        f = _make_filter([".MD", ".QMD"])  # config uses uppercase
        p = tmp_path / "post.md"
        assert p in f.filter([p])


# ---------------------------------------------------------------------------
# filter (bulk API)
# ---------------------------------------------------------------------------

class TestFilter:
    def test_returns_only_matching_files(self, tmp_path: Path):
        files = [
            tmp_path / "a.md",
            tmp_path / "b.png",
            tmp_path / "c.qmd",
            tmp_path / "d.pdf",
        ]
        f = _make_filter([".md", ".qmd"])
        result = f.filter(files)
        assert result == [tmp_path / "a.md", tmp_path / "c.qmd"]

    def test_empty_list_returns_empty(self):
        f = _make_filter([".md"])
        assert f.filter([]) == []

    def test_empty_extensions_keeps_all(self, tmp_path: Path):
        files = [tmp_path / "a.md", tmp_path / "b.png"]
        f = _make_filter([])
        assert f.filter(files) == files

    def test_no_match_returns_empty(self, tmp_path: Path):
        files = [tmp_path / "a.png", tmp_path / "b.jpg"]
        f = _make_filter([".md"])
        assert f.filter(files) == []

    def test_all_match_returns_all(self, tmp_path: Path):
        files = [tmp_path / "a.md", tmp_path / "b.md"]
        f = _make_filter([".md"])
        assert f.filter(files) == files

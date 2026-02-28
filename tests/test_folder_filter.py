"""Tests for FolderFilter."""

from pathlib import Path

import pytest

from publishmd.filters.folder_filter import FolderFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_filter(included_folders: list) -> FolderFilter:
    return FolderFilter({"included_folders": included_folders})


# ---------------------------------------------------------------------------
# filter – per-file / single-item cases
# ---------------------------------------------------------------------------

class TestFilterSingleFile:
    def test_file_inside_included_folder_kept(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        f = _make_filter(["posts"])
        p = posts / "article.md"
        assert p in f.filter([p])

    def test_file_outside_all_folders_dropped(self, tmp_path: Path):
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        f = _make_filter(["posts"])
        p = drafts / "draft.md"
        assert p not in f.filter([p])

    def test_empty_included_list_keeps_all(self, tmp_path: Path):
        f = _make_filter([])
        p = tmp_path / "anything" / "file.md"
        assert p in f.filter([p])

    def test_nested_included_path(self, tmp_path: Path):
        deep = tmp_path / "content" / "published"
        deep.mkdir(parents=True)
        f = _make_filter(["content/published"])
        p = deep / "post.md"
        assert p in f.filter([p])

    def test_file_in_sibling_dropped(self, tmp_path: Path):
        posts = tmp_path / "posts"
        other = tmp_path / "other"
        posts.mkdir()
        other.mkdir()
        f = _make_filter(["posts"])
        p = other / "file.md"
        assert p not in f.filter([p])

    def test_multiple_included_folders(self, tmp_path: Path):
        posts = tmp_path / "posts"
        pages = tmp_path / "pages"
        drafts = tmp_path / "drafts"
        for d in (posts, pages, drafts):
            d.mkdir()
        f = _make_filter(["posts", "pages"])
        assert (posts / "a.md") in f.filter([posts / "a.md"])
        assert (pages / "b.md") in f.filter([pages / "b.md"])
        assert (drafts / "c.md") not in f.filter([drafts / "c.md"])


# ---------------------------------------------------------------------------
# filter (bulk API)
# ---------------------------------------------------------------------------

class TestFilter:
    def test_keeps_only_files_in_included_folders(self, tmp_path: Path):
        posts = tmp_path / "posts"
        drafts = tmp_path / "drafts"
        posts.mkdir()
        drafts.mkdir()
        files = [posts / "a.md", drafts / "b.md", posts / "c.md"]
        f = _make_filter(["posts"])
        result = f.filter(files)
        assert result == [posts / "a.md", posts / "c.md"]

    def test_empty_list_returns_empty(self):
        f = _make_filter(["posts"])
        assert f.filter([]) == []

    def test_empty_included_list_keeps_all(self, tmp_path: Path):
        files = [tmp_path / "a" / "x.md", tmp_path / "b" / "y.md"]
        f = _make_filter([])
        assert f.filter(files) == files

    def test_no_match_returns_empty(self, tmp_path: Path):
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        files = [drafts / "a.md"]
        f = _make_filter(["posts"])
        assert f.filter(files) == []

    def test_all_match_returns_all(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        files = [posts / "a.md", posts / "b.md"]
        f = _make_filter(["posts"])
        assert f.filter(files) == files

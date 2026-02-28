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


# ---------------------------------------------------------------------------
# include_root option
# ---------------------------------------------------------------------------

def _make_filter_with_root(included_folders: list) -> FolderFilter:
    return FolderFilter({"included_folders": included_folders, "include_root": True})


class TestIncludeRoot:
    def test_root_file_kept_with_include_root(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        root_file = tmp_path / "index.md"
        sub_file = posts / "post.md"
        f = _make_filter_with_root(["posts"])
        result = f.filter([root_file, sub_file])
        assert root_file in result
        assert sub_file in result

    def test_root_file_dropped_without_include_root(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        root_file = tmp_path / "index.md"
        sub_file = posts / "post.md"
        f = _make_filter(["posts"])
        result = f.filter([root_file, sub_file])
        assert root_file not in result
        assert sub_file in result

    def test_include_root_only_no_subfolders(self, tmp_path: Path):
        # include_root=True, no included_folders → only root files kept
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        root_file = tmp_path / "readme.md"
        sub_file = drafts / "draft.md"
        f = FolderFilter({"include_root": True, "included_folders": []})
        result = f.filter([root_file, sub_file])
        assert root_file in result
        assert sub_file not in result

    def test_include_root_with_multiple_subfolders(self, tmp_path: Path):
        posts = tmp_path / "posts"
        pages = tmp_path / "pages"
        other = tmp_path / "other"
        for d in (posts, pages, other):
            d.mkdir()
        root_file = tmp_path / "index.md"
        f = _make_filter_with_root(["posts", "pages"])
        result = f.filter([root_file, posts / "a.md", pages / "b.md", other / "c.md"])
        assert root_file in result
        assert (posts / "a.md") in result
        assert (pages / "b.md") in result
        assert (other / "c.md") not in result

    def test_nested_file_not_considered_root(self, tmp_path: Path):
        # A file at depth 2 should NOT be treated as a root file
        posts = tmp_path / "posts"
        deep = posts / "deep"
        deep.mkdir(parents=True)
        root_file = tmp_path / "index.md"
        deep_file = deep / "article.md"
        f = FolderFilter({"include_root": True, "included_folders": []})
        result = f.filter([root_file, deep_file])
        assert root_file in result
        assert deep_file not in result

    def test_empty_file_list(self):
        f = _make_filter_with_root(["posts"])
        assert f.filter([]) == []

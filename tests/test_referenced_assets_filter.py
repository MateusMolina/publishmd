"""Tests for ReferencedAssetsFilter."""

from pathlib import Path
from typing import List

import pytest

from publishmd.filters.referenced_assets_filter import ReferencedAssetsFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_filter(**kwargs) -> ReferencedAssetsFilter:
    return ReferencedAssetsFilter(kwargs)


def _write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# _find_common_parent
# ---------------------------------------------------------------------------

class TestFindCommonParent:
    def test_single_file(self, tmp_path: Path):
        f = tmp_path / "a" / "file.md"
        result = ReferencedAssetsFilter._find_common_parent([f])
        assert result == (tmp_path / "a").resolve()

    def test_siblings(self, tmp_path: Path):
        a = tmp_path / "a.md"
        b = tmp_path / "b.md"
        result = ReferencedAssetsFilter._find_common_parent([a, b])
        assert result == tmp_path.resolve()

    def test_empty_returns_none(self):
        assert ReferencedAssetsFilter._find_common_parent([]) is None


# ---------------------------------------------------------------------------
# filter – basic cases
# ---------------------------------------------------------------------------

class TestFilter:
    def test_unreferenced_asset_is_dropped(self, tmp_path: Path):
        md = _write(tmp_path / "doc.md", "# Hello")
        img = _write(tmp_path / "unused.png")
        f = _make_filter()
        result = f.filter([md, img])
        assert md in result
        assert img not in result

    def test_referenced_asset_is_kept(self, tmp_path: Path):
        img = _write(tmp_path / "hero.png")
        md = _write(tmp_path / "doc.md", "![Hero](hero.png)")
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result

    def test_no_assets_returns_all_files(self, tmp_path: Path):
        md1 = _write(tmp_path / "a.md", "# A")
        md2 = _write(tmp_path / "b.md", "# B")
        f = _make_filter()
        result = f.filter([md1, md2])
        assert set(result) == {md1, md2}

    def test_empty_list_returns_empty(self):
        f = _make_filter()
        assert f.filter([]) == []

    def test_other_files_always_kept(self, tmp_path: Path):
        yaml = _write(tmp_path / "config.yaml", "key: value")
        img = _write(tmp_path / "unused.png")
        f = _make_filter()
        result = f.filter([yaml, img])
        assert yaml in result
        assert img not in result


# ---------------------------------------------------------------------------
# filter – link pattern variations
# ---------------------------------------------------------------------------

class TestLinkPatterns:
    def test_html_img_tag(self, tmp_path: Path):
        img = _write(tmp_path / "photo.jpg")
        md = _write(tmp_path / "doc.md", '<img src="photo.jpg" alt="x">')
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result

    def test_markdown_link_to_pdf(self, tmp_path: Path):
        pdf = _write(tmp_path / "report.pdf")
        md = _write(tmp_path / "index.md", "[Download PDF](report.pdf)")
        f = _make_filter()
        result = f.filter([md, pdf])
        assert pdf in result

    def test_wikilink_image(self, tmp_path: Path):
        img = _write(tmp_path / "diagram.png")
        md = _write(tmp_path / "doc.md", "![[diagram.png]]")
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result

    def test_wikilink_without_extension(self, tmp_path: Path):
        img = _write(tmp_path / "chart.png")
        md = _write(tmp_path / "doc.md", "![[chart]]")
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result

    def test_url_not_resolved(self, tmp_path: Path):
        img = _write(tmp_path / "remote.png")
        md = _write(tmp_path / "doc.md", "![x](https://example.com/remote.png)")
        f = _make_filter()
        # img is not a referenced local file
        result = f.filter([md, img])
        assert img not in result

    def test_multiple_references_in_one_file(self, tmp_path: Path):
        img1 = _write(tmp_path / "a.png")
        img2 = _write(tmp_path / "b.jpg")
        img3 = _write(tmp_path / "c.svg")
        md = _write(
            tmp_path / "doc.md",
            "![a](a.png)\n![b](b.jpg)\n# No c here",
        )
        f = _make_filter()
        result = f.filter([md, img1, img2, img3])
        assert img1 in result
        assert img2 in result
        assert img3 not in result


# ---------------------------------------------------------------------------
# filter – subdirectory references
# ---------------------------------------------------------------------------

class TestSubdirectoryReferences:
    def test_relative_path_with_subdirectory(self, tmp_path: Path):
        assets = tmp_path / "assets"
        assets.mkdir()
        img = _write(assets / "logo.png")
        md = _write(tmp_path / "doc.md", "![logo](assets/logo.png)")
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result

    def test_asset_referenced_from_subdir_file(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        img = _write(tmp_path / "img.png")
        md = _write(src / "doc.md", "![img](../img.png)")
        f = _make_filter()
        result = f.filter([md, img])
        assert img in result


# ---------------------------------------------------------------------------
# filter – custom config
# ---------------------------------------------------------------------------

class TestCustomConfig:
    def test_custom_text_extensions(self, tmp_path: Path):
        img = _write(tmp_path / "diagram.png")
        # Use a markdown-style reference that the filter's regex patterns can detect
        txt = _write(tmp_path / "notes.rst", "![diagram](diagram.png)")
        # RST not in default text_extensions; with custom config it is
        f = _make_filter(text_extensions=[".rst"], asset_extensions=[".png"])
        # rst file should be scanned and the reference found
        result = f.filter([txt, img])
        assert img in result

    def test_custom_asset_extensions(self, tmp_path: Path):
        csv = _write(tmp_path / "data.csv")
        md = _write(tmp_path / "doc.md", "[data](data.csv)")
        f = _make_filter(asset_extensions=[".csv"])
        result = f.filter([md, csv])
        assert csv in result

    def test_non_asset_file_not_treated_as_asset(self, tmp_path: Path):
        css = _write(tmp_path / "style.css", "body {}")
        md = _write(tmp_path / "doc.md", "# No css reference")
        f = _make_filter()  # .css not in default asset_extensions
        result = f.filter([md, css])
        # css is "other" → always kept
        assert css in result

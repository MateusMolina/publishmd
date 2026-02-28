"""Tests for Filter.sanity_check() behaviour."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.base import FilterSanityError
from publishmd.filters.frontmatter_filter import FrontmatterFilter
from publishmd.filters.extension_filter import ExtensionFilter
from publishmd.filters.ignorefolder_filter import IgnoreFolderFilter
from publishmd.filters.folder_filter import FolderFilter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Default behaviour: sanity_check is opt-in
# ---------------------------------------------------------------------------

class TestSanityCheckDisabledByDefault:
    """sanity_check is a no-op unless 'sanity_check: true' is in the config."""

    def test_disabled_by_default_frontmatter(self, tmp_path: Path):
        # A file that does NOT satisfy the filter criteria is in the output.
        # With sanity_check disabled this must NOT raise.
        f = FrontmatterFilter({"publish": True})
        bad = _write(tmp_path / "private.md", "---\npublish: false\n---")
        f.sanity_check([bad])  # should not raise

    def test_disabled_by_default_extension(self, tmp_path: Path):
        f = ExtensionFilter({"extensions": [".md"]})
        bad = tmp_path / "image.png"
        f.sanity_check([bad])  # should not raise

    def test_enabled_false_explicitly(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": False})
        bad = _write(tmp_path / "private.md", "---\npublish: false\n---")
        f.sanity_check([bad])  # should not raise


# ---------------------------------------------------------------------------
# FrontmatterFilter sanity check
# ---------------------------------------------------------------------------

class TestFrontmatterSanityCheck:
    def test_passes_when_all_files_match(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        good = _write(tmp_path / "ok.md", "---\npublish: true\n---\n# Hi")
        f.sanity_check([good])  # should not raise

    def test_passes_when_output_is_empty(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        f.sanity_check([])  # should not raise

    def test_passes_with_non_markdown_files(self, tmp_path: Path):
        # Non-markdown files pass through FrontmatterFilter unconditionally.
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        img = tmp_path / "image.png"
        img.write_bytes(b"")
        f.sanity_check([img])  # should not raise

    def test_fails_when_excluded_file_is_in_output(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        bad = _write(tmp_path / "private.md", "---\npublish: false\n---\n# Private")
        with pytest.raises(FilterSanityError) as exc_info:
            f.sanity_check([bad])
        assert "private.md" in str(exc_info.value)

    def test_fails_reports_all_violations(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        good = _write(tmp_path / "good.md", "---\npublish: true\n---\n# Good")
        bad1 = _write(tmp_path / "private1.md", "---\npublish: false\n---\n# Bad")
        bad2 = _write(tmp_path / "private2.md", "---\npublish: false\n---\n# Bad")
        with pytest.raises(FilterSanityError) as exc_info:
            f.sanity_check([good, bad1, bad2])
        msg = str(exc_info.value)
        assert str(bad1) in msg
        assert str(bad2) in msg
        assert str(good) not in msg

    def test_error_message_mentions_filter_class(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        bad = _write(tmp_path / "bad.md", "---\npublish: false\n---")
        with pytest.raises(FilterSanityError) as exc_info:
            f.sanity_check([bad])
        assert "FrontmatterFilter" in str(exc_info.value)

    def test_works_with_qmd_extension_after_rename(self, tmp_path: Path):
        # Simulates ChangeExtensionTransformer having renamed .md → .qmd.
        # The frontmatter is still present; FrontmatterFilter checks .qmd too.
        f = FrontmatterFilter({"publish": True, "sanity_check": True})
        good = _write(tmp_path / "ok.qmd", "---\npublish: true\n---\n# Hi")
        bad = _write(tmp_path / "private.qmd", "---\npublish: false\n---")
        with pytest.raises(FilterSanityError):
            f.sanity_check([good, bad])

    def test_multiple_criteria_flags_partial_mismatch(self, tmp_path: Path):
        f = FrontmatterFilter({"publish": True, "status": "ready", "sanity_check": True})
        partial = _write(tmp_path / "partial.md", "---\npublish: true\nstatus: draft\n---")
        with pytest.raises(FilterSanityError):
            f.sanity_check([partial])


# ---------------------------------------------------------------------------
# ExtensionFilter sanity check
# ---------------------------------------------------------------------------

class TestExtensionSanityCheck:
    def test_passes_when_all_files_match(self, tmp_path: Path):
        f = ExtensionFilter({"extensions": [".md", ".qmd"], "sanity_check": True})
        files = [tmp_path / "a.md", tmp_path / "b.qmd"]
        f.sanity_check(files)  # should not raise

    def test_fails_when_wrong_extension_present(self, tmp_path: Path):
        f = ExtensionFilter({"extensions": [".md"], "sanity_check": True})
        with pytest.raises(FilterSanityError) as exc_info:
            f.sanity_check([tmp_path / "image.png"])
        assert "ExtensionFilter" in str(exc_info.value)

    def test_empty_extensions_always_passes(self, tmp_path: Path):
        f = ExtensionFilter({"extensions": [], "sanity_check": True})
        f.sanity_check([tmp_path / "anything.xyz"])  # should not raise


# ---------------------------------------------------------------------------
# IgnoreFolderFilter sanity check
# ---------------------------------------------------------------------------

class TestIgnoreFolderSanityCheck:
    def test_passes_when_no_ignored_folder_present(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        f = IgnoreFolderFilter({"ignored_folders": ["drafts"], "sanity_check": True})
        f.sanity_check([posts / "a.md"])  # should not raise

    def test_fails_when_ignored_folder_present(self, tmp_path: Path):
        drafts = tmp_path / "drafts"
        drafts.mkdir()
        f = IgnoreFolderFilter({"ignored_folders": ["drafts"], "sanity_check": True})
        with pytest.raises(FilterSanityError) as exc_info:
            f.sanity_check([drafts / "private.md"])
        assert "IgnoreFolderFilter" in str(exc_info.value)


# ---------------------------------------------------------------------------
# FolderFilter sanity check
# ---------------------------------------------------------------------------

class TestFolderSanityCheck:
    def test_passes_when_all_in_included(self, tmp_path: Path):
        posts = tmp_path / "posts"
        posts.mkdir()
        f = FolderFilter({"included_folders": ["posts"], "sanity_check": True})
        f.sanity_check([posts / "a.md"])  # should not raise

    def test_fails_when_file_outside_included(self, tmp_path: Path):
        other = tmp_path / "other"
        other.mkdir()
        f = FolderFilter({"included_folders": ["posts"], "sanity_check": True})
        with pytest.raises(FilterSanityError):
            f.sanity_check([other / "file.md"])


# ---------------------------------------------------------------------------
# Processor integration: sanity check wired in
# ---------------------------------------------------------------------------

class TestProcessorSanityCheck:
    """Verify that Processor.process() propagates FilterSanityError."""

    def test_processor_succeeds_when_sanity_check_passes(self, tmp_path: Path):
        """Happy path: all output files satisfy the filter criteria."""
        import yaml
        from publishmd.processor import Processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write(input_dir / "good.md", "---\npublish: true\n---\n# Good")
        _write(input_dir / "also-good.md", "---\npublish: true\n---\n# Also good")

        config_data = {
            "filters": [
                {
                    "name": "fm",
                    "type": "publishmd.filters.frontmatter_filter.FrontmatterFilter",
                    "config": {"publish": True, "sanity_check": True},
                }
            ],
            "transformers": [],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        output_dir = tmp_path / "output"
        processor = Processor(str(config_file))
        processor.process(input_dir, output_dir)  # must not raise

        assert (output_dir / "good.md").exists()
        assert (output_dir / "also-good.md").exists()

    def test_processor_raises_on_sanity_violation(self, tmp_path: Path):
        """Sanity failure: tamper with output after copy to simulate a leaked file."""
        import yaml
        from publishmd.base import FilterSanityError
        from publishmd.processor import Processor
        from unittest.mock import patch

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write(input_dir / "good.md", "---\npublish: true\n---\n# Good")

        config_data = {
            "filters": [
                {
                    "name": "fm",
                    "type": "publishmd.filters.frontmatter_filter.FrontmatterFilter",
                    "config": {"publish": True, "sanity_check": True},
                }
            ],
            "transformers": [],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        output_dir = tmp_path / "output"
        processor = Processor(str(config_file))

        # Intercept _copy_files to inject a "leaked" private file into the output
        original_copy = processor._copy_files

        def copy_with_leak(files, in_dir, out_dir):
            copied = original_copy(files, in_dir, out_dir)
            # Inject a file that should not be there
            leaked = out_dir / "private.md"
            leaked.write_text("---\npublish: false\n---\n# private")
            copied.append(leaked)
            return copied

        with patch.object(processor, "_copy_files", side_effect=copy_with_leak):
            with pytest.raises(FilterSanityError) as exc_info:
                processor.process(input_dir, output_dir)

        assert "private.md" in str(exc_info.value)

    def test_processor_nested_frontmatter_survives_stale_links_transformer(
        self, tmp_path: Path
    ):
        """Regression: StaleLinksTransformer must not mangle YAML frontmatter.

        A file whose frontmatter contains a URL nested four spaces inside a
        list item (e.g. ``author[].url``) was previously corrupted by the
        transformer's 'collapse 3+ spaces' pass.  The resulting invalid YAML
        made FrontmatterFilter unable to read ``publish: true``, so the sanity
        check raised FilterSanityError even though the file should pass.
        """
        import yaml
        from publishmd.processor import Processor

        input_dir = tmp_path / "input"
        input_dir.mkdir()
        _write(
            input_dir / "article.md",
            "---\n"
            "author:\n"
            "  - name: Test Author\n"
            "    url: https://example.com\n"
            "publish: true\n"
            "---\n\n"
            "# Article\n\n"
            "Some text with a [stale link](missing.md) that will be removed.\n",
        )

        config_data = {
            "filters": [
                {
                    "name": "fm",
                    "type": "publishmd.filters.frontmatter_filter.FrontmatterFilter",
                    "config": {"publish": True, "sanity_check": True},
                }
            ],
            "transformers": [
                {
                    "name": "stale_links",
                    "type": "publishmd.transformers.stale_links_transformer.StaleLinksTransformer",
                    "config": {"remove_stale_links": True, "convert_to_text": False},
                }
            ],
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        output_dir = tmp_path / "output"
        processor = Processor(str(config_file))
        # Must not raise FilterSanityError
        processor.process(input_dir, output_dir)

        out_file = output_dir / "article.md"
        assert out_file.exists()
        result = out_file.read_text()
        # Indentation in frontmatter must be intact
        assert "    url: https://example.com" in result

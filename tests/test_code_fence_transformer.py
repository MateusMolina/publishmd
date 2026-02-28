"""Tests for CodeFenceTransformer."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.transformers.code_fence_transformer import CodeFenceTransformer


class TestCodeFenceTransformerInit:
    def test_default_languages(self):
        t = CodeFenceTransformer({})
        assert "mermaid" in t.languages
        assert "plantuml" in t.languages

    def test_custom_languages(self):
        t = CodeFenceTransformer({"languages": ["dot", "tikz"]})
        assert t.languages == ["dot", "tikz"]

    def test_empty_languages(self):
        t = CodeFenceTransformer({"languages": []})
        assert t.languages == []


class TestCodeFenceTransformerTransform:
    def _transform(self, content: str, config: dict = None) -> str:
        t = CodeFenceTransformer(config or {})
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "doc.md"
            f.write_text(content, encoding="utf-8")
            t.transform(f, [f])
            return f.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Basic conversion
    # ------------------------------------------------------------------

    def test_converts_mermaid_fence(self):
        result = self._transform("```mermaid\ngraph LR\nA-->B\n```\n")
        assert "```{mermaid}" in result

    def test_converts_plantuml_fence(self):
        result = self._transform("```plantuml\n@startuml\n@enduml\n```\n")
        assert "```{plantuml}" in result

    def test_converts_configured_language(self):
        result = self._transform(
            "```dot\ndigraph G {}\n```\n",
            {"languages": ["dot"]},
        )
        assert "```{dot}" in result

    def test_content_body_preserved(self):
        body = "graph LR\nA-->B\n"
        result = self._transform(f"```mermaid\n{body}```\n")
        assert body in result

    # ------------------------------------------------------------------
    # Already-converted fences must not be double-wrapped
    # ------------------------------------------------------------------

    def test_does_not_double_wrap_brace_fence(self):
        result = self._transform("```{mermaid}\ngraph LR\n```\n")
        assert result.count("{mermaid}") == 1
        assert "{{mermaid}}" not in result

    # ------------------------------------------------------------------
    # Non-targeted languages left untouched
    # ------------------------------------------------------------------

    def test_non_targeted_language_untouched(self):
        original = "```python\nprint('hi')\n```\n"
        result = self._transform(original)
        assert result == original

    def test_only_configured_languages_converted(self):
        t = CodeFenceTransformer({"languages": ["mermaid"]})
        with TemporaryDirectory() as tmp:
            f = Path(tmp) / "doc.md"
            content = "```mermaid\nchart\n```\n\n```plantuml\ndiag\n```\n"
            f.write_text(content)
            t.transform(f, [f])
            result = f.read_text()
        assert "```{mermaid}" in result
        assert "```plantuml" in result  # plantuml must be unchanged

    # ------------------------------------------------------------------
    # Multiple fences in one file
    # ------------------------------------------------------------------

    def test_multiple_fences_converted(self):
        content = (
            "# Doc\n"
            "```mermaid\ngraph LR\nA-->B\n```\n"
            "Some text\n"
            "```mermaid\nsequenceDiagram\n```\n"
        )
        result = self._transform(content)
        assert result.count("```{mermaid}") == 2

    def test_mixed_fences(self):
        content = (
            "```mermaid\ngraph\n```\n"
            "```plantuml\ndiag\n```\n"
        )
        result = self._transform(content)
        assert "```{mermaid}" in result
        assert "```{plantuml}" in result

    # ------------------------------------------------------------------
    # Indented fences (e.g. inside lists)
    # ------------------------------------------------------------------

    def test_indented_fence_converted(self):
        content = "- item\n\n  ```mermaid\n  graph\n  ```\n"
        result = self._transform(content)
        assert "```{mermaid}" in result

    # ------------------------------------------------------------------
    # Backtick variants (4 backticks)
    # ------------------------------------------------------------------

    def test_four_backtick_fence_converted(self):
        result = self._transform("````mermaid\ngraph\n````\n")
        assert "````{mermaid}" in result

    # ------------------------------------------------------------------
    # File skipping
    # ------------------------------------------------------------------

    def test_non_text_file_skipped(self, tmp_path):
        bin_file = tmp_path / "image.png"
        bin_file.write_bytes(b"\x00\x01\x02\x03")
        t = CodeFenceTransformer({})
        t.transform(bin_file, [bin_file])
        # Should not raise and file content unchanged
        assert bin_file.read_bytes() == b"\x00\x01\x02\x03"

    def test_nonexistent_file_skipped(self, tmp_path):
        t = CodeFenceTransformer({})
        t.transform(tmp_path / "ghost.md", [])  # must not raise

    # ------------------------------------------------------------------
    # No unnecessary write
    # ------------------------------------------------------------------

    def test_no_write_when_no_changes(self, tmp_path):
        f = tmp_path / "doc.md"
        content = "```python\nprint('hi')\n```\n"
        f.write_text(content)
        mtime_before = f.stat().st_mtime_ns
        CodeFenceTransformer({}).transform(f, [f])
        assert f.stat().st_mtime_ns == mtime_before

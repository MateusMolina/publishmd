"""Test QMD emitter functionality."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.emitters.qmd_emitter import QmdEmitter


class TestQmdEmitter:
    def test_init(self):
        """Test QMD emitter initialization."""
        config = {
            "file_extensions": [".md", ".markdown"],
        }
        emitter = QmdEmitter(config)

        assert emitter.file_extensions == [".md", ".markdown"]

    def test_init_defaults(self):
        """Test QMD emitter initialization with defaults."""
        emitter = QmdEmitter({})

        assert emitter.file_extensions == [".md", ".markdown", ".qmd"]

    def test_emit_files_with_filtered_list(self):
        """Test emitting only files provided in filtered list."""
        content1 = """---
publish: true
---

# Test Document 1

This should be emitted.
"""

        content2 = """---
publish: false
---

# Test Document 2

This should not be emitted.
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()
            test_file1 = input_dir / "test1.md"
            test_file2 = input_dir / "test2.md"
            test_file1.write_text(content1)
            test_file2.write_text(content2)

            # Only provide test1 in filtered list
            filtered_files = [test_file1]  # Changed from set to list

            emitter = QmdEmitter({})
            emitted_files = emitter.emit(filtered_files, output_dir)  # New API

            # Should only emit the filtered file
            assert len(emitted_files) == 1
            assert emitted_files[0] == output_dir / "test1.qmd"
            assert emitted_files[0].exists()

    def test_emit_files_no_filtered_list(self):
        """Test emitting all files when provided in the list."""
        content = """# Test Document

This should be emitted.
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()
            test_file = input_dir / "test.md"
            test_file.write_text(content)

            emitter = QmdEmitter({})
            emitted_files = emitter.emit(
                [test_file], output_dir
            )  # New API - pass list of files

            # Should emit the provided file
            assert len(emitted_files) == 1
            assert emitted_files[0] == output_dir / "test.qmd"
            assert emitted_files[0].exists()

    def test_get_output_path(self):
        """Test getting output path with correct extension."""
        emitter = QmdEmitter({})

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()
            test_file = input_dir / "test.md"

            output_path = emitter._get_output_path(test_file, input_dir, output_dir)

            assert output_path == output_dir / "test.qmd"

    def test_emit_files(self):
        """Test emitting files to output directory."""
        content = """---
publish: true
---

# Test Document

This is a test.
"""

        with TemporaryDirectory() as temp_dir:
            input_dir = Path(temp_dir) / "input"
            output_dir = Path(temp_dir) / "output"

            input_dir.mkdir()
            test_file = input_dir / "test.md"
            test_file.write_text(content)

            emitter = QmdEmitter({})
            emitted_files = emitter.emit([test_file], output_dir)  # New API

            assert len(emitted_files) == 1
            assert emitted_files[0] == output_dir / "test.qmd"
            assert emitted_files[0].exists()
            assert emitted_files[0].read_text() == content

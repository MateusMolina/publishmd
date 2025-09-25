"""Integration tests for publishmd.

These tests validate the complete pipeline from input to output using
golden master/snapshot testing approach.

Each configN.yaml has a corresponding configN-output/ golden master.
To regenerate golden master:
    publishmd -c tests/integration/config1.yaml -i tests/integration/example -o tests/integration/config1-output
"""

import pytest
import shutil
import filecmp
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Tuple

from publishmd.processor import Processor


@pytest.mark.integration
class TestIntegrationPipeline:
    """Integration tests using golden master approach for multiple configurations."""

    @pytest.fixture
    def integration_dir(self) -> Path:
        """Get path to integration test directory."""
        return Path(__file__).parent

    @pytest.fixture
    def example_dir(self, integration_dir: Path) -> Path:
        """Get path to example content."""
        return integration_dir / "example"

    def get_config_scenarios(self, integration_dir: Path) -> List[Tuple[str, str]]:
        """Get all config scenarios (config file, expected output dir)."""
        scenarios = []
        for config_file in integration_dir.glob("config*.yaml"):
            config_name = config_file.stem  # e.g., "config1"
            expected_output_dir = integration_dir / f"{config_name}-output"
            if expected_output_dir.exists():
                scenarios.append((str(config_file), str(expected_output_dir)))
        return scenarios

    def test_all_config_scenarios(self, integration_dir: Path, example_dir: Path):
        """Test all available config scenarios."""
        scenarios = self.get_config_scenarios(integration_dir)
        assert len(scenarios) > 0, "No config scenarios found"

        for config_file_str, expected_output_dir_str in scenarios:
            config_file = Path(config_file_str)
            expected_output_dir = Path(expected_output_dir_str)

            with TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Copy input content to temporary location
                input_dir = temp_path / "input"
                shutil.copytree(example_dir, input_dir)

                # Set up actual output directory
                actual_output_dir = temp_path / "actual_output"

                # Run processor with specific config
                processor = Processor(str(config_file))
                processor.process(input_dir, actual_output_dir)

                # Compare directory structures recursively
                self._assert_directories_equal(
                    actual_output_dir, expected_output_dir, config_name=config_file.stem
                )
        """Test that each config scenario produces expected output."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Copy input content to temporary location
            input_dir = temp_path / "input"
            shutil.copytree(example_dir, input_dir)

            # Set up actual output directory
            actual_output_dir = temp_path / "actual_output"

            # Run processor with specific config
            processor = Processor(str(config_file))
            processor.process(input_dir, actual_output_dir)

            # Compare directory structures recursively
            self._assert_directories_equal(
                actual_output_dir, expected_output_dir, config_name=config_file.stem
            )

    def _assert_directories_equal(
        self, actual_dir: Path, expected_dir: Path, config_name: str = "unknown"
    ):
        """
        Recursively compare two directory trees for exact equality.

        Args:
            actual_dir: Directory with actual output
            expected_dir: Directory with expected output (golden master)
            config_name: Name of config for better error messages
        """
        # Check that both directories exist
        assert (
            actual_dir.exists()
        ), f"Actual output directory {actual_dir} does not exist (config: {config_name})"
        assert (
            expected_dir.exists()
        ), f"Expected output directory {expected_dir} does not exist (config: {config_name})"

        # Get all files in both directories
        actual_files = self._get_all_relative_files(actual_dir)
        expected_files = self._get_all_relative_files(expected_dir)

        # Check that the same files exist
        assert actual_files == expected_files, (
            f"File lists differ for {config_name}.\n"
            f"Actual files: {sorted(actual_files)}\n"
            f"Expected files: {sorted(expected_files)}\n"
            f"Missing from actual: {sorted(expected_files - actual_files)}\n"
            f"Extra in actual: {sorted(actual_files - expected_files)}"
        )

        # Compare each file content
        for relative_path in sorted(actual_files):
            actual_file = actual_dir / relative_path
            expected_file = expected_dir / relative_path

            self._assert_files_equal(
                actual_file, expected_file, relative_path, config_name
            )

    def _get_all_relative_files(self, directory: Path) -> set:
        """Get all files in directory as relative paths."""
        files = set()
        for item in directory.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(directory)
                files.add(relative_path)
        return files

    def _assert_files_equal(
        self,
        actual_file: Path,
        expected_file: Path,
        relative_path: Path,
        config_name: str,
    ):
        """Compare two files for exact equality with helpful error messages."""
        # Check that both files exist
        assert (
            actual_file.exists()
        ), f"Actual file {relative_path} does not exist (config: {config_name})"
        assert (
            expected_file.exists()
        ), f"Expected file {relative_path} does not exist (config: {config_name})"

        # For text files, compare content with detailed diff
        if self._is_text_file(actual_file):
            actual_content = actual_file.read_text(encoding="utf-8")
            expected_content = expected_file.read_text(encoding="utf-8")

            if actual_content != expected_content:
                # Create detailed diff for debugging
                import difflib

                diff = "\n".join(
                    difflib.unified_diff(
                        expected_content.splitlines(keepends=True),
                        actual_content.splitlines(keepends=True),
                        fromfile=f"expected/{relative_path}",
                        tofile=f"actual/{relative_path}",
                        lineterm="",
                    )
                )

                assert False, (
                    f"File content differs: {relative_path} (config: {config_name})\n"
                    f"Diff:\n{diff}"
                )
        else:
            # For binary files, compare bytes
            actual_content = actual_file.read_bytes()
            expected_content = expected_file.read_bytes()

            assert actual_content == expected_content, (
                f"Binary file content differs: {relative_path} (config: {config_name})\n"
                f"Actual size: {len(actual_content)} bytes\n"
                f"Expected size: {len(expected_content)} bytes"
            )

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is likely a text file."""
        text_extensions = {
            ".qmd",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".json",
            ".html",
            ".css",
            ".js",
        }
        return file_path.suffix.lower() in text_extensions


@pytest.mark.integration
@pytest.mark.slow
class TestIntegrationScenarios:
    """Additional integration test scenarios for edge cases."""

    @pytest.fixture
    def integration_dir(self) -> Path:
        return Path(__file__).parent

    def test_empty_input_graceful_handling(self, integration_dir: Path):
        """Test that empty input is handled gracefully."""
        # Use first available config for testing
        config_files = list(integration_dir.glob("config*.yaml"))
        if not config_files:
            pytest.skip("No config files found for testing")

        config_path = config_files[0]

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            input_dir = temp_path / "input"
            input_dir.mkdir()

            output_dir = temp_path / "output"

            processor = Processor(str(config_path))
            processor.process(input_dir, output_dir)

            # Should create output directory but with minimal content
            assert output_dir.exists()
            qmd_files = list(output_dir.glob("**/*.qmd"))
            assert len(qmd_files) == 0

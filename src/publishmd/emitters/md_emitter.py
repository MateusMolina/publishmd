"""MD emitter - emits markdown files with a configurable output extension."""

from pathlib import Path
from typing import Any, Dict, List

from ..base import Emitter


class MdEmitter(Emitter):
    """Emitter that copies markdown files with a configurable output extension."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the MD emitter.

        Args:
            config: Configuration dictionary supporting:
                - file_extensions: list of input extensions to process (default [".md", ".markdown", ".qmd"])
                - output_extension: extension for output files (default ".md")
        """
        super().__init__(config)
        self.file_extensions = config.get(
            "file_extensions", [".md", ".markdown", ".qmd"]
        )
        output_ext = config.get("output_extension", ".md")
        if not output_ext.startswith("."):
            output_ext = f".{output_ext}"
        self.output_extension = output_ext

    def emit(self, files_to_process: List[Path], output_dir: Path) -> List[Path]:
        """
        Emit markdown files with the configured output extension.

        Args:
            files_to_process: List of files to process and emit
            output_dir: Target directory for output files

        Returns:
            List of paths to emitted files
        """
        emitted_files = []

        for file_path in files_to_process:
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                input_dir = self._find_common_parent(files_to_process)
                output_path = self._get_output_path(file_path, input_dir, output_dir)
                self._copy_file(file_path, output_path)
                emitted_files.append(output_path)

        return emitted_files

    def _find_common_parent(self, file_paths: List[Path]) -> Path:
        """
        Find the common parent directory of a list of file paths.

        Args:
            file_paths: List of file paths

        Returns:
            Common parent directory
        """
        if not file_paths:
            return Path.cwd()

        if len(file_paths) == 1:
            return file_paths[0].parent

        common_parts = file_paths[0].resolve().parts

        for file_path in file_paths[1:]:
            file_parts = file_path.resolve().parts
            common_len = 0
            for i, (part1, part2) in enumerate(zip(common_parts, file_parts)):
                if part1 == part2:
                    common_len = i + 1
                else:
                    break
            common_parts = common_parts[:common_len]

        return Path(*common_parts) if common_parts else Path("/")

    def _get_output_path(
        self, file_path: Path, input_dir: Path, output_dir: Path
    ) -> Path:
        """
        Get the output path for a file, applying the configured output extension.

        Args:
            file_path: Original file path
            input_dir: Input directory
            output_dir: Output directory

        Returns:
            Output path with the configured extension
        """
        file_path = file_path.resolve()
        input_dir = input_dir.resolve()
        # Do NOT resolve output_dir so callers' path objects are preserved
        output_dir = Path(output_dir)

        try:
            relative_path = file_path.relative_to(input_dir)
        except ValueError:
            relative_path = Path(file_path.name)

        output_path = output_dir / relative_path
        output_path = output_path.with_suffix(self.output_extension)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def _copy_file(self, input_path: Path, output_path: Path) -> None:
        """
        Copy a file to the output path.

        Args:
            input_path: Source file path
            output_path: Destination file path
        """
        content = input_path.read_text(encoding="utf-8")
        output_path.write_text(content, encoding="utf-8")

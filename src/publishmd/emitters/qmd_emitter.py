"""QMD emitter - emits markdown files as Quarto files with frontmatter filtering."""

from pathlib import Path
from typing import Any, Dict, List

from ..base import Emitter


class QmdEmitter(Emitter):
    """Emitter that converts markdown files to Quarto format."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the QMD emitter."""
        super().__init__(config)
        self.file_extensions = config.get(
            "file_extensions", [".md", ".markdown", ".qmd"]
        )

    def emit(self, files_to_process: List[Path], output_dir: Path) -> List[Path]:
        """
        Emit markdown files as QMD files.

        Args:
            files_to_process: List of files to process and emit
            output_dir: Target directory for QMD files

        Returns:
            List of paths to emitted QMD files
        """
        emitted_files = []

        for file_path in files_to_process:
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Calculate input directory from the first file (assuming all files share a common root)
                if files_to_process and len(files_to_process) > 0:
                    # Find the common parent directory of all input files
                    input_dir = self._find_common_parent(files_to_process)
                else:
                    input_dir = file_path.parent

                output_path = self._get_output_path(file_path, input_dir, output_dir)
                self._copy_and_convert_file(file_path, output_path)
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

        # Start with the first file's parents
        common_parts = file_paths[0].resolve().parts

        # Find common parts with all other files
        for file_path in file_paths[1:]:
            file_parts = file_path.resolve().parts
            # Find the length of the common prefix
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
        Get the output path for a file, changing extension to .qmd.

        Args:
            file_path: Original file path
            input_dir: Input directory
            output_dir: Output directory

        Returns:
            Output path with .qmd extension
        """
        # Ensure paths are absolute for proper comparison
        file_path = file_path.resolve()
        input_dir = input_dir.resolve()
        output_dir = output_dir.resolve()

        try:
            relative_path = file_path.relative_to(input_dir)
        except ValueError:
            # If file is not in input_dir, use just the filename
            relative_path = file_path.name

        output_path = output_dir / relative_path

        # Change extension to .qmd
        output_path = output_path.with_suffix(".qmd")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def _copy_and_convert_file(self, input_path: Path, output_path: Path) -> None:
        """
        Copy and convert a markdown file to QMD format.

        Args:
            input_path: Source file path
            output_path: Destination file path
        """
        content = input_path.read_text(encoding="utf-8")

        # QMD content is the same as markdown
        # Future enhancements could add QMD-specific transformations

        output_path.write_text(content, encoding="utf-8")

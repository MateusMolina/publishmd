"""Core processor that orchestrates emitters, transformers, and filters."""

from pathlib import Path
from typing import Any, Dict, List, Set

from .base import Emitter, Transformer, Filter
from .config import ConfigLoader, PluginLoader


class Processor:
    """Main processor that orchestrates the conversion process."""

    def __init__(self, config_path: Path, cli_overrides: Dict[str, Any] = None):
        """
        Initialize the processor with configuration.

        Args:
            config_path: Path to the YAML configuration file
            cli_overrides: Optional dictionary of CLI parameter overrides
        """
        self.config = ConfigLoader.load_config(config_path)
        ConfigLoader.validate_config(self.config)

        # Apply CLI overrides if provided
        if cli_overrides:
            self._apply_cli_overrides(cli_overrides)

        self.emitters = self._load_emitters()
        self.transformers = self._load_transformers()
        self.filters = self._load_filters()

    def _apply_cli_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply CLI parameter overrides to the configuration."""
        # This could be extended to support more sophisticated override logic
        pass

    def _load_emitters(self) -> List[Emitter]:
        """Load emitter instances from configuration."""
        emitter_configs = self.config.get("emitters", [])
        return PluginLoader.load_emitters(emitter_configs)

    def _load_transformers(self) -> List[Transformer]:
        """Load transformer instances from configuration."""
        transformer_configs = self.config.get("transformers", [])
        return PluginLoader.load_transformers(transformer_configs)

    def _load_filters(self) -> List[Filter]:
        """Load filter instances from configuration."""
        filter_configs = self.config.get("filters", [])
        return PluginLoader.load_filters(filter_configs)

    def process(self, input_dir: Path, output_dir: Path) -> None:
        """
        Process markdown files from input directory to output directory.

        Args:
            input_dir: Source directory containing markdown files
            output_dir: Target directory for processed files
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)

        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 0: Apply global filter to determine which files should be processed
        filtered_files = self._filter_files(input_dir)

        # Step 1: Run all emitters with the filtered file list
        all_emitted_files = []
        for emitter in self.emitters:
            emitted_files = emitter.emit(filtered_files, output_dir)
            all_emitted_files.extend(emitted_files)

        # Step 2: Run all transformers on emitted files
        for transformer in self.transformers:
            for file_path in all_emitted_files:
                if file_path.exists():
                    transformer.transform(file_path, all_emitted_files)

        print(
            f"Processing complete. Filtered {len(filtered_files)} files, "
            f"emitted {len(all_emitted_files)} files to {output_dir}"
        )

    def _filter_files(self, input_dir: Path) -> List[Path]:
        """
        Filter all files based on all configured filters.

        Args:
            input_dir: Input directory to scan for files

        Returns:
            List of files that pass all filters
        """
        filtered_files = []

        for file_path in input_dir.rglob("*"):
            if file_path.is_file():
                # If no filters are configured, include all files
                if not self.filters:
                    filtered_files.append(file_path)
                    continue

                # File must pass all filters to be included
                include_file = True
                for filter_instance in self.filters:
                    if not filter_instance.should_include(file_path):
                        include_file = False
                        break

                if include_file:
                    filtered_files.append(file_path)

        return filtered_files

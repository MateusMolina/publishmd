"""Core processor that orchestrates transformers and filters."""

import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import Transformer, Filter
from .config import ConfigLoader, PluginLoader


class Processor:
    """Main processor that orchestrates the conversion process.

    Pipeline:
      1. Collect every file under ``input_dir`` recursively.
      2. Apply filters to reduce the list (files that fail any filter are dropped).
      3. Copy every remaining file to ``output_dir``, preserving directory structure.
      4. Apply transformers in order to every copied file.
         Transformers that rename files (e.g. ``ChangeExtensionTransformer``)
         should update the ``copied_files`` list in-place so that subsequent
         transformers see the updated paths.
    """

    def __init__(self, config_path: Path, cli_overrides: Dict[str, Any] = None):
        """
        Initialize the processor with configuration.

        Args:
            config_path: Path to the YAML configuration file
            cli_overrides: Optional dictionary of CLI parameter overrides
        """
        self._config_path = Path(config_path)
        self.config = ConfigLoader.load_config(config_path)
        ConfigLoader.validate_config(self.config)

        # Resolve optional directories from config (relative to the config file)
        config_dir = self._config_path.parent
        self.input_dir: Path | None = (
            (config_dir / self.config["input_dir"]).resolve()
            if "input_dir" in self.config
            else None
        )
        self.output_dir: Path | None = (
            (config_dir / self.config["output_dir"]).resolve()
            if "output_dir" in self.config
            else None
        )

        # Apply CLI overrides if provided
        if cli_overrides:
            self._apply_cli_overrides(cli_overrides)

        self.transformers = self._load_transformers()
        self.filters = self._load_filters()

    def _apply_cli_overrides(self, overrides: Dict[str, Any]) -> None:
        """Apply CLI parameter overrides to the configuration."""
        if overrides.get("input_dir") is not None:
            self.input_dir = Path(overrides["input_dir"]).resolve()
        if overrides.get("output_dir") is not None:
            self.output_dir = Path(overrides["output_dir"]).resolve()

    def _load_transformers(self) -> List[Transformer]:
        """Load transformer instances from configuration."""
        transformer_configs = self.config.get("transformers", [])
        return PluginLoader.load_transformers(transformer_configs)

    def _load_filters(self) -> List[Filter]:
        """Load filter instances from configuration."""
        filter_configs = self.config.get("filters", [])
        return PluginLoader.load_filters(filter_configs)

    def process(self, input_dir: Path = None, output_dir: Path = None) -> None:
        """
        Process files from input directory to output directory.

        Args:
            input_dir: Source directory.  Falls back to ``input_dir`` in config.
            output_dir: Target directory.  Falls back to ``output_dir`` in config.
        """
        input_dir = (
            Path(input_dir).resolve() if input_dir is not None else self.input_dir
        )
        output_dir = Path(output_dir) if output_dir is not None else self.output_dir

        if input_dir is None:
            raise ValueError(
                "input_dir must be provided via CLI argument or 'input_dir' in the config file"
            )
        if output_dir is None:
            raise ValueError(
                "output_dir must be provided via CLI argument or 'output_dir' in the config file"
            )

        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Collect all files, then apply filters
        filtered_files = self._filter_files(input_dir)

        # Step 2: Copy every filtered file to output_dir preserving structure
        copied_files = self._copy_files(filtered_files, input_dir, output_dir)

        # Step 3: Run all transformers on the copied files
        for transformer in self.transformers:
            for file_path in list(copied_files):
                if file_path.exists():
                    transformer.transform(file_path, copied_files)

        print(
            f"Processing complete. Copied {len(copied_files)} files "
            f"({len(filtered_files)} passed filters) to {output_dir}"
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _filter_files(self, input_dir: Path) -> List[Path]:
        """Return every file under *input_dir* that passes all configured filters.

        Filters are applied sequentially; each filter receives the output of the
        previous one so an early filter can shrink the list seen by later filters.
        """
        files: List[Path] = sorted(
            f for f in input_dir.rglob("*") if f.is_file()
        )
        for f in self.filters:
            files = f.filter(files)
        return files

    def _copy_files(
        self, files: List[Path], input_dir: Path, output_dir: Path
    ) -> List[Path]:
        """Copy *files* to *output_dir*, preserving directory structure relative
        to *input_dir*.  Returns the list of output (copied) paths."""
        copied: List[Path] = []

        for src in files:
            try:
                relative = src.resolve().relative_to(input_dir)
            except ValueError:
                relative = Path(src.name)

            dst = Path(output_dir) / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(dst)

        return copied

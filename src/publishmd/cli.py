"""Command-line interface for publishmd."""

import click
from pathlib import Path
from typing import Dict, Any

from .processor import Processor


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the YAML configuration file",
)
@click.option(
    "--input-dir",
    "-i",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    required=True,
    help="Input directory containing markdown files",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory for processed files",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def main(config: Path, input_dir: Path, output_dir: Path, verbose: bool) -> None:
    """Prepare markdown content for publication."""

    if verbose:
        click.echo(f"Loading configuration from: {config}")
        click.echo(f"Input directory: {input_dir}")
        click.echo(f"Output directory: {output_dir}")

    try:
        # Create CLI overrides dictionary
        cli_overrides: Dict[str, Any] = {
            "verbose": verbose,
        }

        # Initialize processor
        processor = Processor(config, cli_overrides)

        if verbose:
            click.echo(f"Loaded {len(processor.emitters)} emitters")
            click.echo(f"Loaded {len(processor.transformers)} transformers")

        # Process files
        processor.process(input_dir, output_dir)

        click.echo("Conversion completed successfully!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()

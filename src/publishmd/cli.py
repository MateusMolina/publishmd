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
    default=None,
    help="Input directory containing markdown files (overrides config file value)",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output directory for processed files (overrides config file value)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def main(config: Path, input_dir: Path, output_dir: Path, verbose: bool) -> None:
    """Prepare markdown content for publication."""

    try:
        # Create CLI overrides dictionary (only set dirs when explicitly provided)
        cli_overrides: Dict[str, Any] = {
            "verbose": verbose,
            "input_dir": input_dir,
            "output_dir": output_dir,
        }

        # Initialize processor
        processor = Processor(config, cli_overrides)

        resolved_input = processor.input_dir
        resolved_output = processor.output_dir

        if verbose:
            click.echo(f"Loading configuration from: {config}")
            click.echo(f"Input directory: {resolved_input}")
            click.echo(f"Output directory: {resolved_output}")
            click.echo(f"Loaded {len(processor.filters)} filters")
            click.echo(f"Loaded {len(processor.transformers)} transformers")

        # Process files (dirs already resolved inside the processor)
        processor.process()

        click.echo("Conversion completed successfully!")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()

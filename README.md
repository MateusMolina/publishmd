# publishmd

[![PyPI](https://img.shields.io/pypi/v/publishmd)](https://pypi.org/project/publishmd/)
[![Docs](https://img.shields.io/badge/docs-pub.mmolina.me%2Fpublishmd-blue)](https://pub.mmolina.me/publishmd/)

Prepare markdown content for publication with configurable processing pipeline.

***Use Case 1.*** Transform an Obsidian vault into publication-ready content for a Quarto blog. Convert wikilinks, filter content, copy assets, and apply transformations to prepare your notes for publishing.

## Installation

```bash
pip install publishmd

# With WebP image conversion support
pip install "publishmd[webp]"
```

## Usage

```bash
publishmd -c _config.yml
publishmd -c _config.yml -i ./vault -o ./dist
```

## Configuration

Create a YAML configuration file to specify the processing pipeline, e.g.:

```yaml
# _config.yml
input_dir: vault
output_dir: dist

filters:
  - name: published_only
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

transformers:
  - name: wikilinks
    type: publishmd.transformers.wikilink_transformer.WikilinkTransformer
    config:
      preserve_aliases: true
      link_extension: ".qmd"
  - name: stale_links
    type: publishmd.transformers.stale_links_transformer.StaleLinksTransformer
    config:
      convert_to_text: true
```

For the full configuration reference and all available filters/transformers, see the [docs](https://pub.mmolina.me/publishmd/).

## Development

```bash
pip install -e ".[dev]"
pytest
```

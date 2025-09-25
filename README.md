# publishmd

Prepare markdown content for publication with configurable processing pipeline.

## Use Cases

1. Transform an Obsidian vault into publication-ready content for a Quarto blog. Convert wikilinks, filter content, copy assets, and apply transformations to prepare your notes for publishing.

## Installation

```bash
pip install -e .
```

## Usage

```bash
publishmd -c config.yaml -i /path/to/markdown -o /path/to/output
```

## Configuration

Create a YAML configuration file to specify the processing pipeline, e.g.:

```yaml
filters:
  - name: frontmatter_filter
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

emitters:
  - name: qmd_emitter
    type: publishmd.emitters.qmd_emitter.QmdEmitter
  - name: assets_emitter
    type: publishmd.emitters.assets_emitter.AssetsEmitter

transformers:
  - name: wikilink_transformer
    type: publishmd.transformers.wikilink_transformer.WikilinkTransformer
    config:
      preserve_aliases: true
      link_extension: ".qmd"
  - name: stale_links_transformer
    type: publishmd.transformers.stale_links_transformer.StaleLinksTransformer
    config:
      remove_stale_links: true
      convert_to_text: true
```

For more examples, please check the integration tests folder (tests/integration).

## Development

```bash
pip install -e ".[dev]"
pytest
```

# publishmd

Prepare markdown content for publication with a configurable processing pipeline.

**Use case.** Transform an Obsidian vault into publication-ready content for a Quarto blog: convert wikilinks, filter private notes, copy referenced assets, and apply any number of text transformations — all driven by a single YAML config file.

---

## Installation

```bash
# Core package
pip install publishmd

# With WebP image conversion support (requires Pillow)
pip install "publishmd[webp]"
```

## Quick start

```bash
publishmd -c _config.yml
publishmd -c _config.yml -i ./vault -o ./site/posts
```

### Minimal config

```yaml
# _config.yml
input_dir: vault
output_dir: site/posts

filters:
  - name: published_only
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

transformers:
  - name: wikilinks
    type: publishmd.transformers.wikilink_transformer.WikilinkTransformer
    config:
      link_extension: ".qmd"

  - name: stale_links
    type: publishmd.transformers.stale_links_transformer.StaleLinksTransformer
    config:
      convert_to_text: true
```

See [Configuration](configuration.md) for the full reference, [Transformers](transformers.md) and [Filters](filters.md) for all available plugins.

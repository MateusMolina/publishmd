# Configuration reference

A publishmd config file is a YAML document.  Pass it to the CLI with `-c`:

```bash
publishmd -c _config.yml
publishmd -c _config.yml -i ./vault -o ./dist   # CLI overrides win
```

---

## Top-level keys

| Key | Type | Description |
|-----|------|-------------|
| `input_dir` | `str` | Source directory (relative to the config file). Can be overridden with `-i`. |
| `output_dir` | `str` | Output directory (relative to the config file). Can be overridden with `-o`. |
| `filters` | `list` | Ordered list of filter plugins to apply before copying. |
| `transformers` | `list` | Ordered list of transformer plugins to run on every copied file. |

---

## Plugin entries

Both `filters` and `transformers` share the same entry shape:

```yaml
- name: <human_readable_label>     # arbitrary, used only in error messages
  type: <dotted.module.ClassName>  # importable Python class
  config:                          # passed verbatim to the plugin __init__
    key: value
```

---

## Pipeline order

```
input_dir
   │
   ▼
[filters applied in order]        ← files that fail any filter are dropped
   │
   ▼
copy surviving files to output_dir
   │
   ▼
[transformers applied in order]   ← each transformer runs on every file
   │
   ▼
output_dir
```

Transformers that rename or convert files (e.g. `ChangeExtensionTransformer`,
`ImageToWebpTransformer`) update the internal file list so subsequent
transformers see the new paths.

---

## Full example

```yaml
input_dir: vault
output_dir: dist/posts

filters:
  - name: published_only
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

  - name: no_drafts
    type: publishmd.filters.ignorefolder_filter.IgnoreFolderFilter
    config:
      ignored_folders:
        - drafts
        - _private

  - name: md_and_assets
    type: publishmd.filters.extension_filter.ExtensionFilter
    config:
      extensions: [.md, .png, .jpg, .jpeg, .gif, .svg, .pdf]

  - name: referenced_assets_only
    type: publishmd.filters.referenced_assets_filter.ReferencedAssetsFilter

transformers:
  - name: images_to_webp
    type: publishmd.transformers.image_to_webp_transformer.ImageToWebpTransformer
    config:
      webp_quality: 85

  - name: wikilinks
    type: publishmd.transformers.wikilink_transformer.WikilinkTransformer
    config:
      link_extension: ".qmd"

  - name: stale_links
    type: publishmd.transformers.stale_links_transformer.StaleLinksTransformer
    config:
      convert_to_text: true

  - name: quarto_fences
    type: publishmd.transformers.code_fence_transformer.CodeFenceTransformer
    config:
      languages: [mermaid, plantuml, dot]

  - name: md_to_qmd
    type: publishmd.transformers.change_extension_transformer.ChangeExtensionTransformer
    config:
      from_extensions: [.md, .markdown]
      to_extension: .qmd

  - name: title_from_header
    type: publishmd.transformers.title_from_header_transformer.TitleFromHeaderTransformer

  - name: tags_to_categories
    type: publishmd.transformers.tags_to_categories_transformer.TagsToCategoriesTransformer
```

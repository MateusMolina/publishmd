# Filters

Filters run **before** files are copied to the output directory.  A file that
fails any filter is dropped entirely — it will not appear in the output and
will not be processed by transformers.

Filters are applied in the order they are listed.  The output of each filter
is the input of the next.

---

## ExtensionFilter

::: publishmd.filters.extension_filter.ExtensionFilter

---

## FolderFilter

::: publishmd.filters.folder_filter.FolderFilter

---

## FrontmatterFilter

::: publishmd.filters.frontmatter_filter.FrontmatterFilter

---

## IgnoreFolderFilter

::: publishmd.filters.ignorefolder_filter.IgnoreFolderFilter

---

## ReferencedAssetsFilter

::: publishmd.filters.referenced_assets_filter.ReferencedAssetsFilter

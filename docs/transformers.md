# Transformers

Transformers run **after** files have been copied to the output directory.
They are applied **in order** to every file in the output.  Most transformers
only touch text files and skip binary assets automatically.

Transformers that rename files (e.g. `ChangeExtensionTransformer`,
`ImageToWebpTransformer`) mutate the shared file list so subsequent
transformers see the updated paths.

---

## ChangeExtensionTransformer

::: publishmd.transformers.change_extension_transformer.ChangeExtensionTransformer

---

## CodeFenceTransformer

::: publishmd.transformers.code_fence_transformer.CodeFenceTransformer

---

## ImageToWebpTransformer

::: publishmd.transformers.image_to_webp_transformer.ImageToWebpTransformer

---

## RenameFrontmatterFieldTransformer

::: publishmd.transformers.rename_frontmatter_field_transformer.RenameFrontmatterFieldTransformer

---

## SpacesToDashesTransformer

::: publishmd.transformers.spaces_to_dashes_transformer.SpacesToDashesTransformer

---

## StaleLinksTransformer

::: publishmd.transformers.stale_links_transformer.StaleLinksTransformer

---

## TagsToCategoriesTransformer

::: publishmd.transformers.tags_to_categories_transformer.TagsToCategoriesTransformer

---

## TitleFromHeaderTransformer

::: publishmd.transformers.title_from_header_transformer.TitleFromHeaderTransformer

---

## WikilinkTransformer

::: publishmd.transformers.wikilink_transformer.WikilinkTransformer

"""Transformers package."""

from .change_extension_transformer import ChangeExtensionTransformer
from .stale_links_transformer import StaleLinksTransformer
from .title_from_header_transformer import TitleFromHeaderTransformer
from .wikilink_transformer import WikilinkTransformer
from .tags_to_categories_transformer import TagsToCategoriesTransformer
from .spaces_to_dashes_transformer import SpacesToDashesTransformer
from .rename_frontmatter_field_transformer import RenameFrontmatterFieldTransformer

__all__ = [
    "ChangeExtensionTransformer",
    "StaleLinksTransformer",
    "TitleFromHeaderTransformer",
    "WikilinkTransformer",
    "TagsToCategoriesTransformer",
    "SpacesToDashesTransformer",
    "RenameFrontmatterFieldTransformer",
]
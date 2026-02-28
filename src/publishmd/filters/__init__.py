"""Filters package for file selection and processing criteria."""

# Import individual filters to make them available at package level
from .extension_filter import ExtensionFilter
from .folder_filter import FolderFilter
from .frontmatter_filter import FrontmatterFilter
from .ignorefolder_filter import IgnoreFolderFilter
from .referenced_assets_filter import ReferencedAssetsFilter

__all__ = [
    "ExtensionFilter",
    "FolderFilter",
    "FrontmatterFilter",
    "IgnoreFolderFilter",
    "ReferencedAssetsFilter",
]

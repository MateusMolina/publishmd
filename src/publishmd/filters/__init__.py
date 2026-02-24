"""Filters package for file selection and processing criteria."""

# Import individual filters to make them available at package level
from .frontmatter_filter import FrontmatterFilter
from .ignorefolder_filter import IgnoreFolderFilter

__all__ = ["FrontmatterFilter", "IgnoreFolderFilter"]

"""Filters package for file selection and processing criteria."""

# Import individual filters to make them available at package level
from .frontmatter_filter import FrontmatterFilter

__all__ = ["FrontmatterFilter"]

"""Test processor functionality with integrated filtering."""

from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.processor import Processor


class TestProcessorWithFiltering:
    def test_processor_with_frontmatter_filter(self):
        """Markdown files that do not satisfy the filter are excluded;
        non-markdown files (assets) always pass through and are copied."""
        config_content = """
filters:
  - name: frontmatter_filter
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

transformers: []
"""
        published_content = """---
title: Published Document
publish: true
---

# Published Document
"""
        draft_content = """---
title: Draft Document
publish: false
---

# Draft Document
"""
        no_front_content = """# No Frontmatter Document
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "config.yaml"
            config_file.write_text(config_content.strip())
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            input_dir.mkdir()
            (input_dir / "published.md").write_text(published_content)
            (input_dir / "draft.md").write_text(draft_content)
            (input_dir / "no_frontmatter.md").write_text(no_front_content)
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "photo.png").write_bytes(b"fake png")
            docs_dir = input_dir / "docs"
            docs_dir.mkdir()
            (docs_dir / "manual.pdf").write_bytes(b"fake pdf")

            processor = Processor(config_file)
            processor.process(input_dir, output_dir)

            assert (output_dir / "published.md").exists()
            assert not (output_dir / "draft.md").exists()
            assert not (output_dir / "no_frontmatter.md").exists()
            assert (output_dir / "images" / "photo.png").exists()
            assert (output_dir / "docs" / "manual.pdf").exists()

    def test_processor_without_filter(self):
        """Without any filter, every file in the input directory is copied."""
        config_content = "transformers: []\n"

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "config.yaml"
            config_file.write_text(config_content.strip())
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            input_dir.mkdir()
            (input_dir / "published.md").write_text("# Published\n")
            (input_dir / "draft.md").write_text("# Draft\n")
            (input_dir / "image.png").write_bytes(b"fake png")

            processor = Processor(config_file)
            processor.process(input_dir, output_dir)

            assert (output_dir / "published.md").exists()
            assert (output_dir / "draft.md").exists()
            assert (output_dir / "image.png").exists()

    def test_processor_with_change_extension_transformer(self):
        """ChangeExtensionTransformer renames .md output files to .qmd."""
        config_content = """
filters:
  - name: frontmatter_filter
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

transformers:
  - name: md_to_qmd
    type: publishmd.transformers.change_extension_transformer.ChangeExtensionTransformer
    config:
      from_extensions:
        - ".md"
      to_extension: ".qmd"
"""
        published_content = """---
title: Published
publish: true
---

# Published
"""
        draft_content = """---
title: Draft
publish: false
---

# Draft
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "config.yaml"
            config_file.write_text(config_content.strip())
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            input_dir.mkdir()
            (input_dir / "published.md").write_text(published_content)
            (input_dir / "draft.md").write_text(draft_content)

            processor = Processor(config_file)
            processor.process(input_dir, output_dir)

            assert (output_dir / "published.qmd").exists()
            assert not (output_dir / "published.md").exists()
            assert not (output_dir / "draft.md").exists()
            assert not (output_dir / "draft.qmd").exists()

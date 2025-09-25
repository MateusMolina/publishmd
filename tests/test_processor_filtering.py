"""Test processor functionality with integrated filtering."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from publishmd.processor import Processor


class TestProcessorWithFiltering:
    def test_processor_with_frontmatter_filter(self):
        """Test that processor applies global frontmatter filter correctly."""
        # Create a temporary config file with frontmatter filter
        config_content = """
filters:
  - name: frontmatter_filter
    type: publishmd.filters.frontmatter_filter.FrontmatterFilter
    config:
      publish: true

emitters:
  - name: qmd_emitter
    type: publishmd.emitters.qmd_emitter.QmdEmitter
    config:
      file_extensions:
        - ".md"
        - ".markdown"

  - name: assets_emitter
    type: publishmd.emitters.assets_emitter.AssetsEmitter
    config:
      asset_extensions:
        - ".png"
        - ".jpg"
        - ".pdf"
      file_extensions:
        - ".md"
        - ".markdown"
        - ".qmd"

transformers: []
"""

        # Files with different frontmatter
        published_content = """---
title: Published Document
publish: true
---

# Published Document

This should be processed.

![Published Image](./images/published.png)
[Published PDF](./docs/published.pdf)
"""

        draft_content = """---
title: Draft Document
publish: false
---

# Draft Document

This should NOT be processed.

![Draft Image](./images/draft.png)
[Draft PDF](./docs/draft.pdf)
"""

        no_frontmatter_content = """# No Frontmatter Document

This should NOT be processed.

![No Frontmatter Image](./images/no_frontmatter.png)
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create config file
            config_file = temp_path / "config.yaml"
            config_file.write_text(config_content.strip())

            # Create input structure
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            input_dir.mkdir()

            # Create markdown files
            (input_dir / "published.md").write_text(published_content)
            (input_dir / "draft.md").write_text(draft_content)
            (input_dir / "no_frontmatter.md").write_text(no_frontmatter_content)

            # Create assets
            images_dir = input_dir / "images"
            images_dir.mkdir()
            (images_dir / "published.png").write_text("published image content")
            (images_dir / "draft.png").write_text("draft image content")
            (images_dir / "no_frontmatter.png").write_text(
                "no frontmatter image content"
            )

            docs_dir = input_dir / "docs"
            docs_dir.mkdir()
            (docs_dir / "published.pdf").write_text("published pdf content")
            (docs_dir / "draft.pdf").write_text("draft pdf content")

            # Process with the processor
            processor = Processor(config_file)
            processor.process(input_dir, output_dir)

            # Check that only published files were processed
            # QMD files
            published_qmd = output_dir / "published.qmd"
            draft_qmd = output_dir / "draft.qmd"
            no_frontmatter_qmd = output_dir / "no_frontmatter.qmd"

            assert published_qmd.exists()
            assert not draft_qmd.exists()
            assert not no_frontmatter_qmd.exists()

            # Assets
            published_image = output_dir / "images" / "published.png"
            draft_image = output_dir / "images" / "draft.png"
            no_frontmatter_image = output_dir / "images" / "no_frontmatter.png"

            published_pdf = output_dir / "docs" / "published.pdf"
            draft_pdf = output_dir / "docs" / "draft.pdf"

            assert published_image.exists()
            assert not draft_image.exists()
            assert not no_frontmatter_image.exists()

            assert published_pdf.exists()
            assert not draft_pdf.exists()

    def test_processor_without_frontmatter_filter(self):
        """Test that processor processes all files when no filter is configured."""
        # Create a temporary config file without frontmatter filter
        config_content = """
emitters:
  - name: qmd_emitter
    type: publishmd.emitters.qmd_emitter.QmdEmitter
    config:
      file_extensions:
        - ".md"
        - ".markdown"

transformers: []
"""

        # Files with different frontmatter
        published_content = """---
title: Published Document
publish: true
---

# Published Document

This should be processed.
"""

        draft_content = """---
title: Draft Document
publish: false
---

# Draft Document

This should also be processed when no filter is set.
"""

        no_frontmatter_content = """# No Frontmatter Document

This should also be processed when no filter is set.
"""

        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create config file
            config_file = temp_path / "config.yaml"
            config_file.write_text(config_content.strip())

            # Create input structure
            input_dir = temp_path / "input"
            output_dir = temp_path / "output"
            input_dir.mkdir()

            # Create markdown files
            (input_dir / "published.md").write_text(published_content)
            (input_dir / "draft.md").write_text(draft_content)
            (input_dir / "no_frontmatter.md").write_text(no_frontmatter_content)

            # Process with the processor
            processor = Processor(config_file)
            processor.process(input_dir, output_dir)

            # Check that all files were processed
            published_qmd = output_dir / "published.qmd"
            draft_qmd = output_dir / "draft.qmd"
            no_frontmatter_qmd = output_dir / "no_frontmatter.qmd"

            assert published_qmd.exists()
            assert draft_qmd.exists()
            assert no_frontmatter_qmd.exists()

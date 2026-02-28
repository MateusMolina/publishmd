# Development

## Setup

```bash
git clone https://github.com/mateusmolina/publishmd
cd publishmd
pip install -e ".[dev,webp]"
```

## Running tests

```bash
pytest                                     # all tests
pytest tests/ --ignore=tests/integration  # unit tests only
pytest tests/integration/ -m integration  # integration tests only
```

## Writing a custom plugin

All transformers extend `publishmd.base.Transformer` and all filters extend
`publishmd.base.Filter`.

### Custom transformer skeleton

```python
from pathlib import Path
from typing import Any, Dict, List
from publishmd.base import Transformer, read_text_safe

class MyTransformer(Transformer):
    """One-line description.

    Config keys:
        my_option (str): What it does. Defaults to ``"default"``.

    Example YAML::

        - name: my_transformer
          type: mypackage.my_module.MyTransformer
          config:
            my_option: hello
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.my_option: str = config.get("my_option", "default")

    def transform(self, file_path: Path, copied_files: List[Path]) -> None:
        if not file_path.exists():
            return
        try:
            content = read_text_safe(file_path)
        except IOError:
            return
        # … modify content …
        file_path.write_text(content, encoding="utf-8")
```

### Custom filter skeleton

```python
from pathlib import Path
from typing import Any, Dict, List
from publishmd.base import Filter

class MyFilter(Filter):
    """One-line description."""

    def filter(self, files: List[Path]) -> List[Path]:
        return [f for f in files if self._keep(f)]

    def _keep(self, path: Path) -> bool:
        return True  # your logic here
```

Reference the class by its fully-qualified import path in `config.yaml`:

```yaml
transformers:
  - name: my_transformer
    type: mypackage.my_module.MyTransformer
    config:
      my_option: hello
```

---

## Bumping the version

```bash
python scripts/bump_version.py patch   # 0.2.1 → 0.2.2
python scripts/bump_version.py minor   # 0.2.1 → 0.3.0
python scripts/bump_version.py major   # 0.2.1 → 1.0.0
python scripts/bump_version.py --set 1.2.3
```

The script edits `pyproject.toml` in place.  Commit and tag to trigger the
release workflow (see below).

## Release process

The shortest path — one command does everything:

```bash
python scripts/bump_version.py minor --release
```

This will:

1. Bump the version in `pyproject.toml`
2. `git add pyproject.toml`
3. `git commit -m "chore: bump version to X.Y.Z"`
4. `git tag vX.Y.Z`
5. `git push`
6. `git push --tags`

The `release.yml` GitHub Actions workflow fires on the tag push and publishes to PyPI.

You can also split the steps if you want to review the commit first:

```bash
python scripts/bump_version.py minor   # edits pyproject.toml only
git diff                               # review
python scripts/bump_version.py --set $(grep '^version' pyproject.toml | cut -d'"' -f2) --release
# or just do it manually:
git commit -am "chore: bump version to X.Y.Z"
git tag vX.Y.Z && git push && git push --tags
```

!!! note "First-time PyPI setup"
    The release workflow uses [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/) (OIDC — no API token needed).
    Before the first release, configure a Trusted Publisher on PyPI:

    1. Go to your PyPI project → **Manage** → **Publishing**.
    2. Add a new publisher:
       - Owner: `mateusmolina`
       - Repository: `publishmd`
       - Workflow: `release.yml`
       - Environment: `pypi`

## Building docs locally

```bash
pip install -e ".[docs]"
mkdocs serve        # live-reload dev server at http://127.0.0.1:8000
mkdocs build        # static site → site/
```

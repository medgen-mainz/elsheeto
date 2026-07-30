"""Checks that the code in ``README.md`` stays in sync with the public API.

``README.md`` is the PyPI landing page, so a stale import there is a visible
defect. These tests parse every fenced ``python`` block, so a renamed or
unexported symbol fails CI instead of shipping.
"""

import ast
import re
from pathlib import Path

import pytest

import elsheeto

PATH_README = Path(__file__).parent.parent.parent / "README.md"

RE_PYTHON_BLOCK = re.compile(r"^```python\n(.*?)^```", re.DOTALL | re.MULTILINE)


def readme_python_blocks() -> list[str]:
    """Return the source of every fenced ``python`` block in the README."""
    return RE_PYTHON_BLOCK.findall(PATH_README.read_text(encoding="utf-8"))


def test_readme_has_python_blocks() -> None:
    """Guard against the extraction regex silently matching nothing."""
    assert readme_python_blocks()


@pytest.mark.parametrize("block", readme_python_blocks())
def test_readme_block_is_valid_python(block: str) -> None:
    """Every README example must at least parse."""
    ast.parse(block)


@pytest.mark.parametrize("block", readme_python_blocks())
def test_readme_imports_resolve(block: str) -> None:
    """Every ``elsheeto`` symbol a README example imports must exist."""
    tree = ast.parse(block)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        if node.module != "elsheeto" and not node.module.startswith("elsheeto."):
            continue
        module = __import__(node.module, fromlist=["_"])
        for alias in node.names:
            assert hasattr(module, alias.name), f"README imports {node.module}.{alias.name}, which does not exist"


def test_public_api_is_importable_from_root() -> None:
    """Everything in ``__all__`` must actually be reachable on the package."""
    for name in elsheeto.__all__:
        assert hasattr(elsheeto, name), f"elsheeto.__all__ lists {name}, which is not importable"

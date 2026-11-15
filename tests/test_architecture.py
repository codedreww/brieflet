"""
Guards the dependency direction from the ADR:

    cli.py / app.py / ui.py / app_pages/  ->  core/  ->  config.py

core/ must never import the entry points. If it does, the bot, MCP server and
Streamlit can't reuse core/ on their own, and cli <-> core imports go circular.
"""

import ast
from pathlib import Path

import pytest

CORE_DIR = Path(__file__).parent.parent / "src" / "brieflet" / "core"
ENTRY_POINTS = {"brieflet.cli", "brieflet.app", "brieflet.ui"}


def imported_modules(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


@pytest.mark.parametrize(
    "path",
    sorted(CORE_DIR.rglob("*.py")),
    ids=lambda path: str(path.relative_to(CORE_DIR)),
)
def test_core_does_not_import_entry_points(path):
    bad = [name for name in imported_modules(path) if name in ENTRY_POINTS]

    assert bad == [], f"{path.name} imports {bad}; core/ must not depend on them"

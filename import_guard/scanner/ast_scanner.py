"""AST 扫描器 — 遍历项目 .py 文件，提取所有顶层 import 语句。"""

import ast
import os
from pathlib import Path
from typing import Set

EXCLUDE_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", ".tox", ".eggs",
    "venv", ".venv", "env", ".env", "node_modules",
    "dist", "build", "egg-info", ".mypy_cache", ".pytest_cache",
}


class ImportVisitor(ast.NodeVisitor):
    """Walk AST and collect imported top-level module names."""

    def __init__(self):
        self.imports: Set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".", 1)[0]
            self.imports.add(top)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            if node.level == 0:
                # absolute import: from a.b import c → "a"
                top = node.module.split(".", 1)[0]
                self.imports.add(top)
            # level > 0 is relative import — skip
        self.generic_visit(node)


def scan_directory(root: str, exclude_dirs: Set[str] = None) -> Set[str]:
    """Recursively scan a directory for .py files and extract imports.

    Args:
        root: Project root path.
        exclude_dirs: Extra directory names to skip.

    Returns:
        Set of top-level import names found in the codebase.
    """
    exclude = EXCLUDE_DIRS | (exclude_dirs or set())
    imports: Set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]

        for fname in filenames:
            if fname.endswith(".py"):
                filepath = os.path.join(dirpath, fname)
                try:
                    imports.update(extract_imports(filepath))
                except (SyntaxError, UnicodeDecodeError):
                    pass  # Skip files that can't be parsed

    return imports


def extract_imports(filepath: str) -> Set[str]:
    """Parse a single Python file and return top-level imports."""
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    # Handle empty files
    if not source.strip():
        return set()

    tree = ast.parse(source, filename=filepath)
    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def scan_files(filepaths: list) -> Set[str]:
    """Scan a list of explicit .py file paths and return combined imports."""
    imports: Set[str] = set()
    for fp in filepaths:
        try:
            imports.update(extract_imports(fp))
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
            pass
    return imports

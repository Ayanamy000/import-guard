"""Diff 引擎 — 计算 used vs installed 的集合差异。"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from ..resolver.package_mapper import import_to_package


@dataclass
class DiffResult:
    """Result of comparing code imports against installed/declared packages."""

    # Packages that are in pip freeze / requirements.txt but NOT imported in code
    unused: Set[str] = field(default_factory=set)

    # Modules that are imported in code but NOT in pip freeze / requirements.txt
    missing: Set[str] = field(default_factory=set)

    # Packages used in code AND declared (good)
    matched: Set[str] = field(default_factory=set)

    # Import names that map to known PyPI packages (resolved)
    resolved_imports: Dict[str, str] = field(default_factory=dict)

    # Standard library modules that appear in imports (informational)
    stdlib_imports: Set[str] = field(default_factory=set)


def compute_diff(
    code_imports: Set[str],
    installed_packages: Set[str],
    stdlib_modules: Set[str],
) -> DiffResult:
    """Core diff: compare code imports to installed packages.

    Args:
        code_imports: Top-level module names found in code via AST scan.
        installed_packages: Normalized package names from pip freeze / requirements.txt.
        stdlib_modules: Standard library top-level module names.

    Returns:
        DiffResult with unused, missing, matched, and resolved mappings.
    """
    result = DiffResult()

    # Separate stdlib from third-party imports
    result.stdlib_imports = code_imports & stdlib_modules
    third_party_imports = code_imports - stdlib_modules

    # Map import names → PyPI package names
    resolved: Dict[str, str] = {}
    pkg_to_import: Dict[str, str] = {}
    for imp in third_party_imports:
        pkg = import_to_package(imp)
        resolved[imp] = pkg
        if pkg not in pkg_to_import:
            pkg_to_import[pkg] = imp

    result.resolved_imports = resolved
    resolved_packages = set(resolved.values())

    # Unused: installed but not imported
    result.unused = installed_packages - resolved_packages

    # Missing: imported but not installed
    result.missing = resolved_packages - installed_packages

    # Matched: installed AND imported
    result.matched = resolved_packages & installed_packages

    return result


def normalize_package_name(name: str) -> str:
    """Normalize a package name for comparison (lowercase, underscores→hyphens)."""
    return name.strip().lower().replace("_", "-")

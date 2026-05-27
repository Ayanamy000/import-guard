"""缺失依赖检测器 — 找出代码中用到了但 requirements.txt 里没写的包（裸奔依赖）。"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class MissingPackage:
    """A package imported in code but missing from the dependency spec."""

    import_name: str
    package_name: str
    suggested_version: Optional[str] = None
    suggested_spec: str = ""


@dataclass
class MissingReport:
    """Report of all missing (undeclared) dependencies."""

    packages: List[MissingPackage]
    total_count: int
    dangerous_count: int = 0

    @property
    def summary(self) -> str:
        if self.total_count == 0:
            return "No missing dependencies — all imports are declared."
        return (
            f"{self.total_count} undeclared dependencies found — "
            f"these packages are imported but not listed in requirements.txt"
        )


def detect_missing(
    missing_package_names: Set[str],
    resolved_imports: Dict[str, str],
    latest_versions: Dict[str, Optional[str]],
) -> MissingReport:
    """Build a detailed report of missing (undeclared) dependencies.

    Args:
        missing_package_names: Set of resolved PyPI package names not declared.
        resolved_imports: Mapping {import_name → package_name}.
        latest_versions: {package_name: latest_version} from PyPI.

    Returns:
        MissingReport with list and stats.
    """
    # Build reverse map: package_name → import_name
    pkg_to_import: Dict[str, str] = {}
    for imp, pkg in resolved_imports.items():
        if pkg not in pkg_to_import:
            pkg_to_import[pkg] = imp

    packages: List[MissingPackage] = []
    for pkg_name in sorted(missing_package_names):
        import_name = pkg_to_import.get(pkg_name, pkg_name)
        version = latest_versions.get(pkg_name)
        spec = f"{pkg_name}=={version}" if version else pkg_name
        packages.append(MissingPackage(
            import_name=import_name,
            package_name=pkg_name,
            suggested_version=version,
            suggested_spec=spec,
        ))

    return MissingReport(
        packages=packages,
        total_count=len(packages),
        dangerous_count=len(packages),  # All missing deps are potentially dangerous
    )

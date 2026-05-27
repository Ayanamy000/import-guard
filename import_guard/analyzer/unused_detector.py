"""未使用依赖检测器 — 找出装了但没用的包。"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class UnusedPackage:
    """A single unused package with optional size/version info."""

    name: str
    version: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class UnusedReport:
    """Report of all discovered unused packages."""

    packages: List[UnusedPackage]
    total_count: int
    total_size_bytes: int
    estimated_savings_mb: float
    estimated_time_saved_seconds: float

    @property
    def summary(self) -> str:
        return (
            f"{self.total_count} unused packages found, "
            f"{self.estimated_savings_mb:.1f} MB potentially removable, "
            f"~{self.estimated_time_saved_seconds:.1f}s install time saved"
        )


def detect_unused(
    unused_names: Set[str],
    freeze_data: Dict[str, str],
    size_data: Dict[str, Optional[int]],
) -> UnusedReport:
    """Build a detailed report of unused packages.

    Args:
        unused_names: Set of package names not used by code.
        freeze_data: {package_name: version} from pip freeze.
        size_data: {package_name: size_bytes} from PyPI metadata.

    Returns:
        UnusedReport with sorted list and aggregate stats.
    """
    packages: List[UnusedPackage] = []
    total_size = 0

    for name in sorted(unused_names):
        version = freeze_data.get(name)
        size = size_data.get(name)
        packages.append(UnusedPackage(name=name, version=version, size_bytes=size))
        total_size += size or 0

    # Convert to MB and time
    total_mb = total_size / (1024 * 1024)
    total_sec = sum(
        (p.size_bytes or 0) / (5 * 1024 * 1024) + 2.0 for p in packages
    )

    return UnusedReport(
        packages=packages,
        total_count=len(packages),
        total_size_bytes=total_size,
        estimated_savings_mb=round(total_mb, 2),
        estimated_time_saved_seconds=round(total_sec, 1),
    )

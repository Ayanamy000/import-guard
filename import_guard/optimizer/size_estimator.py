"""体积 / 安装时间预估器 — 估算精简后能节省多少空间和时间。"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SizeEstimate:
    """Estimated savings for removing a set of packages."""

    total_bytes: int
    total_mb: float
    package_count: int
    install_time_seconds: float
    breakdown: Dict[str, Optional[int]]


def estimate_savings(
    package_names: List[str],
    size_data: Dict[str, Optional[int]],
) -> SizeEstimate:
    """Compute total savings from removing a list of packages.

    Args:
        package_names: List of package names to consider for removal.
        size_data: {package_name: size_in_bytes} mapping.

    Returns:
        SizeEstimate with aggregate stats and per-package breakdown.
    """
    breakdown: Dict[str, Optional[int]] = {}
    total = 0
    known_count = 0

    for pkg in package_names:
        size = size_data.get(pkg)
        breakdown[pkg] = size
        if size is not None:
            total += size
            known_count += 1

    total_mb = total / (1024 * 1024)

    # Rough install time: each package ~2s overhead + download time at ~5 MB/s
    install_time = sum(
        2.0 + ((size_data.get(p, 0) or 0) / (5 * 1024 * 1024))
        for p in package_names
    )

    return SizeEstimate(
        total_bytes=total,
        total_mb=round(total_mb, 2),
        package_count=len(package_names),
        install_time_seconds=round(install_time, 1),
        breakdown=breakdown,
    )


def estimate_docker_savings(
    size_estimate: SizeEstimate,
    layer_count: int = 1,
) -> Dict[str, float]:
    """Estimate the impact on Docker image size.

    Rough heuristic: each removed package reduces the image layer proportionally.
    Layer compression typically reduces the diff, so actual savings are ~60-80%
    of the raw package size.
    """
    return {
        "raw_savings_mb": size_estimate.total_mb,
        "estimated_image_savings_mb": round(size_estimate.total_mb * 0.7, 2),
        "build_time_saved_seconds": round(size_estimate.install_time_seconds * 0.85, 1),
        "layers_affected": layer_count,
    }

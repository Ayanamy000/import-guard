"""元数据解析器 — 从 PyPI JSON API 获取包体积、依赖、版本等信息。"""

import json
import time
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PYPI_JSON_URL = "https://pypi.org/pypi/{package}/json"
REQUEST_TIMEOUT = 10


def _fetch_pypi_json(package_name: str) -> Optional[dict]:
    """Fetch package metadata from PyPI JSON API."""
    url = PYPI_JSON_URL.format(package=package_name)
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError):
        return None


def get_package_size(package_name: str) -> Optional[int]:
    """Estimate installed size of the latest version (bytes).

    Uses the most recent sdist or wheel file size as a rough proxy.
    Returns None if unavailable.
    """
    data = _fetch_pypi_json(package_name)
    if not data:
        return None

    files = data.get("urls", [])
    if not files:
        return None

    # Prefer wheel size, fallback to sdist
    max_size = 0
    for f in files:
        size = f.get("size", 0)
        if size and size > max_size:
            max_size = size
    return max_size if max_size > 0 else None


def get_latest_version(package_name: str) -> Optional[str]:
    """Get the latest version string for a PyPI package."""
    data = _fetch_pypi_json(package_name)
    if not data:
        return None
    return data.get("info", {}).get("version")


def get_package_info(package_name: str) -> Dict[str, Any]:
    """Fetch combined metadata for a package.

    Returns a dict with keys: name, version, size_bytes, requires_dist, summary.
    """
    data = _fetch_pypi_json(package_name)
    if not data:
        return {"name": package_name, "error": "Package not found on PyPI"}

    info = data.get("info", {})
    files = data.get("urls", [])
    max_size = max((f.get("size", 0) or 0) for f in files) if files else 0

    return {
        "name": package_name,
        "version": info.get("version"),
        "summary": info.get("summary", ""),
        "requires_dist": info.get("requires_dist") or [],
        "size_bytes": max_size or None,
    }


def batch_get_sizes(package_names: set, delay: float = 0.1) -> Dict[str, Optional[int]]:
    """Fetch sizes for a batch of packages from PyPI.

    Includes a small delay between requests to be polite to PyPI.
    """
    sizes: Dict[str, Optional[int]] = {}
    for name in sorted(package_names):
        sizes[name] = get_package_size(name)
        time.sleep(delay)
    return sizes


def estimate_install_time(size_bytes: int) -> float:
    """Crude estimate of install time based on package size.

    Assumes ~5 MB/s download + some overhead. Returns seconds.
    """
    download_sec = size_bytes / (5 * 1024 * 1024)  # 5 MB/s
    overhead = 2.0  # pip resolve + unpack overhead per package
    return round(download_sec + overhead, 2)


def format_size(bytes_val: Optional[int]) -> str:
    """Human-readable size string."""
    if bytes_val is None:
        return "unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"

"""JSON 输出 — 机器可读的报告格式，适合 CI 管道。"""

import json
from typing import Any, Dict, Optional, Set

from ..analyzer.diff_engine import DiffResult
from ..analyzer.unused_detector import UnusedReport
from ..analyzer.missing_detector import MissingReport


def build_json_report(
    diff: DiffResult,
    unused_report: UnusedReport,
    missing_report: MissingReport,
    project_root: str = ".",
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construct a JSON-serializable report dict."""

    report = {
        "meta": {
            "tool": "import-guard",
            "project_root": project_root,
            **(extra_meta or {}),
        },
        "summary": {
            "total_code_imports": len(diff.resolved_imports),
            "total_installed": len(diff.matched) + len(diff.unused),
            "matched_count": len(diff.matched),
            "unused_count": unused_report.total_count,
            "missing_count": missing_report.total_count,
            "stdlib_count": len(diff.stdlib_imports),
            "estimated_savings_mb": unused_report.estimated_savings_mb,
            "estimated_time_saved_seconds": unused_report.estimated_time_saved_seconds,
        },
        "unused": [
            {
                "name": p.name,
                "version": p.version,
                "size_bytes": p.size_bytes,
            }
            for p in unused_report.packages
        ],
        "missing": [
            {
                "import_name": p.import_name,
                "package_name": p.package_name,
                "suggested_version": p.suggested_version,
                "suggested_spec": p.suggested_spec,
            }
            for p in missing_report.packages
        ],
        "matched": sorted(diff.matched),
        "stdlib_imports": sorted(diff.stdlib_imports),
        "resolved_imports": dict(sorted(diff.resolved_imports.items())),
    }

    return report


def write_json_report(
    diff: DiffResult,
    unused_report: UnusedReport,
    missing_report: MissingReport,
    output_path: str,
    project_root: str = ".",
) -> None:
    """Write full JSON report to a file."""
    data = build_json_report(diff, unused_report, missing_report, project_root)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def print_json_report(
    diff: DiffResult,
    unused_report: UnusedReport,
    missing_report: MissingReport,
    project_root: str = ".",
) -> None:
    """Print JSON report to stdout."""
    data = build_json_report(diff, unused_report, missing_report, project_root)
    print(json.dumps(data, indent=2, ensure_ascii=False))

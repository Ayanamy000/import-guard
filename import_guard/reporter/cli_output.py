"""终端输出 — 带颜色的 CLI 报告。"""

import sys
from typing import Dict, Optional, Set

from ..analyzer.diff_engine import DiffResult
from ..analyzer.unused_detector import UnusedReport
from ..analyzer.missing_detector import MissingReport
from ..resolver.metadata_resolver import format_size

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Symbols — use ASCII-safe characters to avoid encoding issues on Windows
_SYM_OK = "[OK]"
_SYM_WARN = "[!!]"
_SYM_ERR = "[XX]"


def _safe_print(*args, **kwargs) -> None:
    """Print with fallback for terminals that can't handle Unicode."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Replace non-ASCII characters and retry
        ascii_args = tuple(
            a.encode("ascii", errors="replace").decode("ascii") if isinstance(a, str) else a
            for a in args
        )
        print(*ascii_args, **kwargs)


def _c(text: str, color: str) -> str:
    """Wrap text in color if stdout is a tty."""
    if sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def print_header(title: str) -> None:
    """Print a bold section header."""
    width = 60
    print()
    print(_c("=" * width, CYAN))
    print(_c(f"  {title}", BOLD + CYAN))
    print(_c("=" * width, CYAN))
    print()


def print_unused_report(report: UnusedReport) -> None:
    """Print the unused-packages report in a table format."""
    print_header("UNUSED DEPENDENCIES (installed but not imported)")

    if not report.packages:
        _safe_print(_c(f"  {_SYM_OK} No unused dependencies found!", GREEN))
        return

    print(f"  {'Package':<30} {'Version':<15} {'Size':>10}")
    print(f"  {'-'*30} {'-'*15} {'-'*10}")
    for pkg in report.packages:
        ver = pkg.version or "?"
        size_str = format_size(pkg.size_bytes) if pkg.size_bytes else "?"
        name_fmt = f"{pkg.name:<30}"
        print(f"  {_c(name_fmt, RED)}{ver:<15}{size_str:>10}")

    print()
    print(f"  Total: {report.total_count} packages")
    print(f"  Est. disk savings: {report.estimated_savings_mb:.1f} MB")
    print(f"  Est. install time saved: {report.estimated_time_saved_seconds:.1f}s")


def print_missing_report(report: MissingReport) -> None:
    """Print the missing-dependency report."""
    print_header("MISSING DEPENDENCIES (imported but not declared)")

    if not report.packages:
        _safe_print(_c(f"  {_SYM_OK} No missing dependencies!", GREEN))
        return

    print(f"  {'Import':<30} {'Package':<30} {'Suggested':>20}")
    print(f"  {'-'*30} {'-'*30} {'-'*20}")
    for pkg in report.packages:
        spec = pkg.suggested_spec or pkg.package_name
        imp_fmt = f"{pkg.import_name:<30}"
        print(f"  {_c(imp_fmt, YELLOW)}{pkg.package_name:<30}{spec:>20}")

    print()
    _safe_print(_c(f"  {_SYM_WARN} {report.total_count} undeclared dependencies — "
                   f"add these to requirements.txt", YELLOW))


def print_summary(
    diff: DiffResult,
    unused_report: UnusedReport,
    missing_report: MissingReport,
) -> None:
    """Print a summary overview."""
    print_header("SCAN SUMMARY")
    print(f"  Packages matched (declared + used):   {_c(str(len(diff.matched)), GREEN)}")
    print(f"  Packages unused (declared, not used): {_c(str(unused_report.total_count), RED)}")
    print(f"  Packages missing (used, not declared):{_c(str(missing_report.total_count), YELLOW)}")
    print()
    print(f"  Standard library imports detected: {len(diff.stdlib_imports)}")
    if diff.stdlib_imports:
        print(f"  ({', '.join(sorted(diff.stdlib_imports)[:10])}"
              f"{'...' if len(diff.stdlib_imports) > 10 else ''})")
    print()
    print(f"  Potential disk savings: {_c(f'{unused_report.estimated_savings_mb:.1f} MB', GREEN)}")
    print(f"  Install time saved:     {_c(f'{unused_report.estimated_time_saved_seconds:.1f}s', GREEN)}")


def print_success(msg: str) -> None:
    _safe_print(f"{_c(_SYM_OK, GREEN)} {msg}")


def print_warning(msg: str) -> None:
    _safe_print(f"{_c(_SYM_WARN, YELLOW)} {msg}")


def print_error(msg: str) -> None:
    _safe_print(f"{_c(_SYM_ERR, RED)} {msg}")

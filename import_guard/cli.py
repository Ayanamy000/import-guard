"""CLI 入口 — import-guard 命令行工具。

Usage:
    import-guard scan <project_dir>        # Full analysis
    import-guard check <project_dir>       # Quick check (exit code only)
    import-guard optimize <project_dir>    # Generate minimal requirements
    import-guard init                      # Generate GitHub Action / pre-commit configs
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Set

from . import __version__
from .scanner.ast_scanner import scan_directory
from .scanner.import_parser import (
    ImportClassifier,
    parse_requirements_txt,
    parse_pip_freeze_output,
)
from .resolver.package_mapper import batch_map_imports
from .resolver.metadata_resolver import batch_get_sizes, get_latest_version, format_size
from .analyzer.diff_engine import compute_diff
from .analyzer.unused_detector import detect_unused
from .analyzer.missing_detector import detect_missing
from .reporter.cli_output import (
    print_header,
    print_unused_report,
    print_missing_report,
    print_summary,
    print_success,
    print_warning,
    print_error,
)
from .reporter.json_output import write_json_report, print_json_report
from .reporter.html_report import write_html_report
from .optimizer.requirements_builder import (
    build_minimal_requirements,
    write_requirements,
    diff_requirements,
)


def _get_freeze_data(use_current: bool = False) -> Dict[str, str]:
    """Get pip freeze data. Uses current env if use_current, else reads from disk."""
    if use_current:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "freeze"],
                capture_output=True, text=True, check=True,
            )
            return parse_pip_freeze_output(result.stdout)
        except subprocess.CalledProcessError as e:
            print_error(f"pip freeze failed: {e}")
            sys.exit(1)
    return {}


def _get_package_versions(packages: Set[str]) -> Dict[str, Optional[str]]:
    """Get latest versions for a set of packages from PyPI."""
    versions: Dict[str, Optional[str]] = {}
    for pkg in sorted(packages):
        versions[pkg] = get_latest_version(pkg)
    return versions


def cmd_scan(args: argparse.Namespace) -> None:
    """Run a full dependency audit and output results."""
    project_root = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_root):
        print_error(f"Directory not found: {project_root}")
        sys.exit(1)

    is_cli = args.format == "cli"

    if is_cli:
        print_header("Import Guard — Dependency Audit")
        print(f"  Project: {project_root}")

    # 1. Scan code imports
    if is_cli:
        print(f"\n  Scanning Python files for imports...")
    extra_exclude = set(args.exclude.split(",")) if args.exclude else set()
    code_imports = scan_directory(project_root, exclude_dirs=extra_exclude)
    if is_cli:
        print(f"  Found {len(code_imports)} unique top-level imports in code.")

    # 2. Resolve installed / declared packages
    if args.requirements:
        req_path = os.path.abspath(args.requirements)
        if is_cli:
            print(f"  Reading declared packages from: {req_path}")
        installed_set = parse_requirements_txt(req_path)
    elif args.freeze:
        if is_cli:
            print(f"  Using pip freeze output...")
        freeze_data = _get_freeze_data(use_current=True)
        installed_set = set(freeze_data.keys())
    else:
        default_req = os.path.join(project_root, "requirements.txt")
        if os.path.exists(default_req):
            if is_cli:
                print(f"  Using project requirements.txt")
            installed_set = parse_requirements_txt(default_req)
        else:
            if is_cli:
                print(f"  No requirements.txt found, using pip freeze...")
            freeze_data = _get_freeze_data(use_current=True)
            installed_set = set(freeze_data.keys())

    freeze_data = _get_freeze_data(use_current=args.freeze or not args.requirements)

    # 3. Classify imports
    classifier = ImportClassifier()

    # 4. Compute diff
    if is_cli:
        print(f"\n  Computing dependency diff...")
    diff = compute_diff(code_imports, installed_set, classifier._stdlib)

    # 5. Fetch package sizes (with throttling, unless --no-network)
    size_data: Dict[str, Optional[int]] = {}
    if not args.no_network and (diff.unused or diff.missing):
        all_to_check = diff.unused | diff.missing
        if is_cli:
            print(f"  Fetching package metadata from PyPI for {len(all_to_check)} packages...")
        size_data = batch_get_sizes(all_to_check, delay=0.2)
    else:
        if args.no_network and is_cli:
            print(f"  Skipping PyPI metadata (--no-network).")

    # 6. Build sub-reports
    unused_report = detect_unused(diff.unused, freeze_data, size_data)
    missing_versions = _get_package_versions(diff.missing) if not args.no_network else {}
    missing_report = detect_missing(diff.missing, diff.resolved_imports, missing_versions)

    # 7. Output
    if args.format == "json":
        print_json_report(diff, unused_report, missing_report, project_root)
    elif args.format == "html":
        html_path = args.output or "import-guard-report.html"
        write_html_report(diff, unused_report, missing_report, html_path,
                          open_browser=args.open)
        print_success(f"HTML report written to: {html_path}")
        if args.open:
            print(f"  Opened in browser.")
    else:
        # CLI output
        print_unused_report(unused_report)
        print_missing_report(missing_report)
        print_summary(diff, unused_report, missing_report)

    # 8. JSON export (sidecar)
    if args.json_output:
        json_path = args.json_output
        write_json_report(diff, unused_report, missing_report, json_path, project_root)
        print_success(f"JSON report saved to: {json_path}")

    # 9. Exit code for CI
    issues = unused_report.total_count + missing_report.total_count
    if args.strict and issues > 0:
        print_error(f"\nStrict mode: {issues} issue(s) found. Exiting with code 1.")
        sys.exit(1)


def cmd_check(args: argparse.Namespace) -> None:
    """Quick check — suitable for CI/pre-commit. Exits non-zero on issues."""
    project_root = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_root):
        print_error(f"Directory not found: {project_root}")
        sys.exit(1)

    code_imports = scan_directory(project_root)
    classifier = ImportClassifier()

    # Get installed packages
    freeze_data = _get_freeze_data(use_current=True)
    installed_set = set(freeze_data.keys())

    diff = compute_diff(code_imports, installed_set, classifier._stdlib)

    issues_found = False

    if diff.unused and not args.ignore_unused:
        issues_found = True
        print_warning(f"Unused packages: {', '.join(sorted(diff.unused))}")

    if diff.missing:
        issues_found = True
        print_warning(f"Missing packages: {', '.join(sorted(diff.missing))}")

    if issues_found:
        if args.strict:
            sys.exit(1)
    else:
        print_success("All dependencies are clean.")


def cmd_optimize(args: argparse.Namespace) -> None:
    """Generate a minimal requirements.txt based on actual code imports."""
    project_root = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_root):
        print_error(f"Directory not found: {project_root}")
        sys.exit(1)

    print_header("Import Guard — Dependency Optimizer")

    # Scan
    code_imports = scan_directory(project_root)
    print(f"  Code imports: {len(code_imports)} top-level modules")

    # Resolve
    req_path = args.requirements or os.path.join(project_root, "requirements.txt")
    if os.path.exists(req_path):
        declared = parse_requirements_txt(req_path)
        print(f"  Current requirements.txt: {len(declared)} packages")
    else:
        declared = set()
        print(f"  No existing requirements.txt found — will build from scratch")

    classifier = ImportClassifier()
    diff = compute_diff(code_imports, declared, classifier._stdlib)

    # Build minimal requirements
    freeze_data = _get_freeze_data(use_current=True)
    missing_list = sorted(diff.missing)

    content = build_minimal_requirements(
        matched_packages=diff.matched,
        freeze_data=freeze_data,
        missing_packages=missing_list,
        pin_versions=args.pin,
    )

    output_path = args.output or "requirements-minimal.txt"
    write_requirements(content, output_path)
    print_success(f"Minimal requirements written to: {output_path}")

    # Show diff stats
    if os.path.exists(req_path):
        d = diff_requirements(req_path, output_path)
        print(f"  Packages removed: {d['removed']}")
        print(f"  Packages added:   {d['added']}")
        print(f"  Packages kept:    {d['kept']}")
        if d["removed"] > 0:
            print(f"  Reduction: {d['removed']} / {d['removed'] + d['kept']} "
                  f"({100 * d['removed'] / (d['removed'] + d['kept']):.0f}%)")


def cmd_init(args: argparse.Namespace) -> None:
    """Generate integration config files."""
    from .integrations.github_action import generate_workflow_file
    from .integrations.pre_commit import get_hook_config

    output_dir = os.path.abspath(args.output_dir) if args.output_dir else os.getcwd()

    if args.github_action:
        workflow_dir = os.path.join(output_dir, ".github", "workflows")
        os.makedirs(workflow_dir, exist_ok=True)
        workflow_path = os.path.join(workflow_dir, "import-guard.yml")
        with open(workflow_path, "w") as f:
            f.write(generate_workflow_file())
        print_success(f"GitHub Action written to: {workflow_path}")

    if args.pre_commit:
        precommit_path = os.path.join(output_dir, ".pre-commit-config.yaml")
        hook_config = get_hook_config()
        if os.path.exists(precommit_path):
            print_warning(f".pre-commit-config.yaml already exists. "
                          f"Add this to it:\n\n{hook_config}\n")
        else:
            with open(precommit_path, "w") as f:
                f.write(hook_config)
            print_success(f"Pre-commit hook config written to: {precommit_path}")

    if args.dockerfile:
        from .integrations.docker_plugin import analyze_dockerfile
        docker_path = os.path.join(output_dir, args.dockerfile)
        if os.path.exists(docker_path):
            # Use empty unused set — user can run full analysis separately
            analysis = analyze_dockerfile(docker_path, set())
            from .integrations.docker_plugin import format_optimizations
            print(format_optimizations(analysis))
        else:
            print_error(f"Dockerfile not found: {docker_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="import-guard",
        description="Dependency audit & optimization tool for Python projects.",
    )
    parser.add_argument(
        "--version", action="version", version=f"import-guard {__version__}"
    )

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # === scan ===
    scan_p = sub.add_parser("scan", help="Run full dependency audit")
    scan_p.add_argument("project_dir", nargs="?", default=".", help="Project root directory")
    scan_p.add_argument("-r", "--requirements", help="Path to requirements.txt")
    scan_p.add_argument("--freeze", action="store_true", help="Use pip freeze instead of requirements.txt")
    scan_p.add_argument("--format", choices=["cli", "json", "html"], default="cli",
                        help="Output format (default: cli)")
    scan_p.add_argument("-o", "--output", help="Output file path (for html format)")
    scan_p.add_argument("--open", action="store_true", help="Open HTML report in browser")
    scan_p.add_argument("--json-output", help="Also save JSON report to file")
    scan_p.add_argument("--exclude", help="Comma-separated extra dirs to skip")
    scan_p.add_argument("--no-network", action="store_true", help="Skip PyPI metadata fetch")
    scan_p.add_argument("--strict", action="store_true", help="Exit code 1 if issues found")
    scan_p.set_defaults(func=cmd_scan)

    # === check ===
    check_p = sub.add_parser("check", help="Quick CI check (no network, exit code only)")
    check_p.add_argument("project_dir", nargs="?", default=".", help="Project root directory")
    check_p.add_argument("--ignore-unused", action="store_true",
                         help="Don't fail on unused packages")
    check_p.add_argument("--strict", action="store_true", help="Exit code 1 on any issue")
    check_p.set_defaults(func=cmd_check)

    # === optimize ===
    opt_p = sub.add_parser("optimize", help="Generate minimal requirements.txt")
    opt_p.add_argument("project_dir", nargs="?", default=".", help="Project root directory")
    opt_p.add_argument("-r", "--requirements", help="Path to existing requirements.txt")
    opt_p.add_argument("-o", "--output", default="requirements-minimal.txt",
                       help="Output path (default: requirements-minimal.txt)")
    opt_p.add_argument("--pin", action="store_true", default=True,
                       help="Pin exact versions (default: True)")
    opt_p.set_defaults(func=cmd_optimize)

    # === init ===
    init_p = sub.add_parser("init", help="Generate integration configs")
    init_p.add_argument("--output-dir", help="Output directory for config files")
    init_p.add_argument("--github-action", action="store_true",
                        help="Generate GitHub Actions workflow")
    init_p.add_argument("--pre-commit", action="store_true",
                        help="Generate .pre-commit-config.yaml snippet")
    init_p.add_argument("--dockerfile", help="Path to Dockerfile for analysis")
    init_p.set_defaults(func=cmd_init)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()

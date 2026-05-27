"""Pre-commit Hook 集成 — 作为 .pre-commit-config.yaml 的 hook 运行。"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

PRE_COMMIT_HOOK_YAML = """\
# Add this to your .pre-commit-config.yaml

repos:
  - repo: local
    hooks:
      - id: import-guard
        name: Import Guard Audit
        entry: import-guard check .
        language: system
        pass_filenames: false
        files: \\.(py|txt)$
        always_run: false
"""


def get_hook_config() -> str:
    """Return the .pre-commit-config.yaml snippet."""
    return PRE_COMMIT_HOOK_YAML.strip()


def run_as_hook(
    project_root: str,
    strict: bool = False,
) -> Tuple[bool, str]:
    """Run import-guard as a pre-commit hook.

    Returns (passed: bool, message: str).
    When strict=True, the hook fails if there are any unused or missing deps.
    """
    # Import here to avoid circular deps
    from ..scanner.ast_scanner import scan_directory
    from ..scanner.import_parser import parse_requirements_txt, parse_pip_freeze_output, ImportClassifier
    from ..analyzer.diff_engine import compute_diff
    from ..resolver.package_mapper import batch_map_imports

    # Scan code imports
    code_imports = scan_directory(project_root)

    # Get installed packages
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True, text=True, check=True,
        )
        freeze_data = parse_pip_freeze_output(result.stdout)
    except subprocess.CalledProcessError:
        freeze_data = {}
    installed = set(freeze_data.keys())

    # Classify
    classifier = ImportClassifier()
    stdlib = classifier._stdlib

    # Diff
    diff = compute_diff(code_imports, installed, stdlib)

    issues = []
    if diff.unused:
        issues.append(f"Unused packages: {', '.join(sorted(diff.unused))}")
    if diff.missing:
        issues.append(f"Missing packages: {', '.join(sorted(diff.missing))}")

    if issues:
        msg = "import-guard: " + "; ".join(issues)
        passed = not strict
        return passed, msg
    else:
        return True, "import-guard: all dependencies clean ✓"

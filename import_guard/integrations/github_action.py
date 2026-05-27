"""GitHub Actions 集成 — 生成 CI workflow 文件和 annotations。"""

from typing import Dict, Any, List, Optional

GITHUB_ACTION_YAML = """\
# GitHub Action: Import Guard — dependency audit
# Add this to .github/workflows/import-guard.yml

name: Import Guard Audit

on:
  pull_request:
    paths:
      - "requirements.txt"
      - "requirements/*.txt"
      - "**/*.py"
  push:
    branches: [main, master]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install import-guard
        run: pip install import-guard

      - name: Install project dependencies
        run: pip install -r requirements.txt

      - name: Run import-guard audit
        run: import-guard scan . --format json --output audit-report.json

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: import-guard-report
          path: audit-report.json

      - name: Check for issues
        run: import-guard check . --strict
"""


def generate_workflow_file() -> str:
    """Return the recommended GitHub Actions workflow YAML content."""
    return GITHUB_ACTION_YAML.strip()


def generate_annotation(
    unused_count: int,
    missing_count: int,
    est_mb: float,
) -> str:
    """Generate a human-readable GitHub Actions annotation message."""
    parts = []
    if unused_count > 0:
        parts.append(f"🚫 {unused_count} unused dependency(s)")
    if missing_count > 0:
        parts.append(f"⚠️ {missing_count} undeclared dependency(s)")
    if not parts:
        return "✅ All dependencies are clean."
    msg = " | ".join(parts)
    if est_mb > 0:
        msg += f" — potential savings: {est_mb:.1f} MB"
    return msg


def build_ci_summary(
    unused_count: int,
    missing_count: int,
    matched_count: int,
    est_mb: float,
    est_time: float,
) -> str:
    """Build a CI-friendly markdown summary string."""
    return f"""\
## 📦 Import Guard Audit

| Category | Count |
|----------|-------|
| ✅ Matched | {matched_count} |
| 🚫 Unused | {unused_count} |
| ⚠️ Missing | {missing_count} |

**Potential Savings:** {est_mb:.1f} MB disk, ~{est_time:.1f}s install time
"""

"""Docker 插件 — 优化 Dockerfile 中的 pip install 层。

分析 Dockerfile 中的 pip install 指令，对比实际依赖，给出优化建议：
- 移除不必要的 COPY requirements.txt
- 精简 pip install 的包列表
- 建议 multi-stage build 策略
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set, Tuple


@dataclass
class DockerOptimization:
    """A single Dockerfile optimization suggestion."""

    line_number: int
    original: str
    suggestion: str
    reason: str


@dataclass
class DockerAnalysis:
    """Result of Dockerfile analysis."""

    dockerfile_path: str
    has_pip_install: bool = False
    has_requirements_copy: bool = False
    pip_install_lines: List[int] = field(default_factory=list)
    optimizations: List[DockerOptimization] = field(default_factory=list)


def analyze_dockerfile(
    dockerfile_path: str,
    unused_packages: Set[str],
) -> DockerAnalysis:
    """Analyze a Dockerfile for optimization opportunities.

    Args:
        dockerfile_path: Path to the Dockerfile.
        unused_packages: Set of unused packages detected by the analyzer.

    Returns:
        DockerAnalysis with optimization suggestions.
    """
    path = Path(dockerfile_path)
    if not path.exists():
        return DockerAnalysis(dockerfile_path=dockerfile_path)

    lines = path.read_text(encoding="utf-8").splitlines()
    analysis = DockerAnalysis(dockerfile_path=dockerfile_path)

    pip_install_pattern = re.compile(
        r'pip\s+install\s+(.*)', re.IGNORECASE
    )

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if "COPY" in stripped and "requirements" in stripped:
            analysis.has_requirements_copy = True

        match = pip_install_pattern.search(stripped)
        if match:
            analysis.has_pip_install = True
            analysis.pip_install_lines.append(i)

            install_target = match.group(1)
            # Check if any unused packages are explicitly pip installed
            for pkg in unused_packages:
                if pkg.lower().replace("-", "_") in install_target.lower():
                    analysis.optimizations.append(DockerOptimization(
                        line_number=i,
                        original=line,
                        suggestion=f"# (removed unused package: {pkg})",
                        reason=f"Remove '{pkg}' from RUN pip install — not used by code",
                    ))

    # If requirements were copied but there are unused packages, suggest
    # generating a minimal requirements before the COPY step
    if analysis.has_requirements_copy and unused_packages:
        analysis.optimizations.append(DockerOptimization(
            line_number=0,
            original="(requirements.txt usage detected in Dockerfile)",
            suggestion=(
                "RUN pip install import-guard && import-guard scan . --optimize "
                "-o requirements-minimal.txt"
            ),
            reason=(
                f"Generate a minimal requirements.txt before COPY to avoid "
                f"installing {len(unused_packages)} unused packages"
            ),
        ))

    return analysis


def generate_docker_snippet(
    minimal_requirements_path: str = "requirements-minimal.txt",
) -> str:
    """Generate an optimized Dockerfile pip install snippet.

    Uses multi-stage pattern to keep the image lean.
    """
    return f"""\
# --- Optimized by import-guard ---

# Stage 1: Build dependencies (optional, for compiled packages)
# FROM python:3.11-slim AS builder
# COPY {minimal_requirements_path} .
# RUN pip install --user -r {minimal_requirements_path}

# Stage 2: Final image
FROM python:3.11-slim AS final

# Copy only minimal requirements
COPY {minimal_requirements_path} .
RUN pip install --no-cache-dir -r {minimal_requirements_path} \\
    && rm {minimal_requirements_path}

# Copy application code
COPY . /app
WORKDIR /app
"""


def format_optimizations(analysis: DockerAnalysis) -> str:
    """Pretty-print Dockerfile optimization suggestions."""
    if not analysis.optimizations:
        return "✅ Dockerfile looks optimized — no suggestions."

    lines_out = [
        f"📦 Dockerfile Analysis: {analysis.dockerfile_path}",
        f"   {len(analysis.optimizations)} optimization(s) available:",
        "",
    ]
    for opt in analysis.optimizations:
        lines_out.append(f"  Line {opt.line_number}: {opt.reason}")
        if opt.line_number > 0:
            lines_out.append(f"    Current:  {opt.original.strip()}")
            lines_out.append(f"    Suggest:  {opt.suggestion.strip()}")
        lines_out.append("")

    return "\n".join(lines_out)

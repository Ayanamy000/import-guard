# import-guard — Dependency Audit & Optimization Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![PyPI version](https://img.shields.io/badge/PyPI-v0.1.0-orange.svg)](https://pypi.org/project/import-guard/)

When `requirements.txt` drifts out of sync with actual code, unused packages bloat Docker images and slow CI/CD pipelines. **import-guard** fixes that.

## Core Features

- **Static AST Scanning** — Parses all `.py` files in your project to extract actually imported top-level modules
- **Dependency Diff** — Compares code imports against `pip freeze` to identify packages that are installed but never used
- **Reverse Audit** — Detects "naked" dependencies: modules imported in code but missing from `requirements.txt`
- **Clean Output** — Generates a minimal `requirements.txt` with estimated disk savings and install time reduction

## Installation

```bash
pip install import-guard
```

## Usage

```bash
# Full audit (CLI output with color)
import-guard scan .

# Compare against current pip freeze
import-guard scan . --freeze

# JSON output (ideal for CI pipelines)
import-guard scan . --format json

# HTML report (open in browser)
import-guard scan . --format html -o report.html --open

# Quick CI check (exits non-zero on issues)
import-guard check . --strict

# Generate a minimal requirements.txt
import-guard optimize . -o requirements-minimal.txt

# Scaffold CI integration configs
import-guard init --github-action --pre-commit
```

## How It Works

```
  Your Project (.py files)          pip freeze / requirements.txt
          │                                    │
          ▼                                    ▼
   ┌─────────────┐                    ┌─────────────────┐
   │ AST Scanner │                    │ Import Parser   │
   │ extract all │                    │ normalize names │
   │ top-level   │                    │ classify stdlib │
   │ imports     │                    │ vs third-party  │
   └──────┬──────┘                    └────────┬────────┘
          │                                    │
          └──────────────┬─────────────────────┘
                         ▼
                  ┌──────────────┐
                  │  Diff Engine │
                  │  compute     │
                  │  set ops     │
                  └──────┬───────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
   ┌────────────┐ ┌────────────┐ ┌──────────────┐
   │  Matched   │ │   Unused   │ │   Missing    │
   │    ✅      │ │    🚫      │ │     ⚠️        │
   │ declared   │ │ installed  │ │ imported     │
   │ & used     │ │ but not    │ │ but not      │
   │            │ │ imported   │ │ declared     │
   └────────────┘ └─────┬──────┘ └──────┬───────┘
                        │               │
                        ▼               ▼
                 ┌─────────────────────────────┐
                 │       Reporter              │
                 │  CLI · JSON · HTML          │
                 │  + size/time savings        │
                 └─────────────────────────────┘
```

## Project Architecture

```
import_guard/
├── scanner/        # AST scanner + import parser
├── resolver/       # Package name mapper + PyPI metadata resolver
├── analyzer/       # Diff engine + unused/missing detectors
├── reporter/       # CLI / JSON / HTML report generators
├── optimizer/      # Requirements builder + size estimator
├── integrations/   # GitHub Action / Pre-commit / Docker
└── cli.py          # CLI entry point
```

## CI Integration

### GitHub Actions

```bash
import-guard init --github-action
```

This generates `.github/workflows/import-guard.yml` that runs on every PR and push to main, uploading an audit report as a build artifact.

### Pre-commit Hook

```bash
import-guard init --pre-commit
```

Adds import-guard to `.pre-commit-config.yaml` so it runs before every commit.

## Example Output

```
[OK] No missing dependencies — all imports are declared.

============================================================
  UNUSED DEPENDENCIES (installed but not imported)
============================================================

  Package     Version   Size
  ----------  --------  ----
  numpy       1.24.0    21.5 MB
  pandas      2.0.1     28.3 MB
  boto3       1.28.0    12.8 MB

  Total: 3 packages
  Est. disk savings: 62.6 MB
  Est. install time saved: 18.5s
```

## License

This project is open-sourced under the [MIT License](https://opensource.org/licenses/MIT).

```
MIT License

Copyright (c) 2025 import-guard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Contributing

Issues and pull requests are welcome. Please make sure your code passes `import-guard check . --strict` 😄

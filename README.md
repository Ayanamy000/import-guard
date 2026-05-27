# import-guard — 依赖体检与精简工具

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![PyPI version](https://img.shields.io/badge/PyPI-v0.1.0-orange.svg)](https://pypi.org/project/import-guard/)

由于 `requirements.txt` 和实际代码严重脱节——装了一堆用不到的包，镜像体积越来越大，CI/CD 时间越来越长——所以编写了本项目。

## 核心功能

- **静态 AST 扫描** — 扫描项目所有 `.py` 文件，提取实际 import 的顶层模块
- **依赖 Diff** — 与 `pip freeze` 输出做对比，揪出"装了但没用"的包
- **反向检查** — 代码中 import 了但 `requirements.txt` 里没写（裸奔依赖）
- **精简输出** — 输出精简后的 `requirements.txt` + 可节省的体积 / 安装时间预估

## 安装

```bash
pip install import-guard
```

## 使用

```bash
# 完整审计
import-guard scan .

# 使用当前 pip freeze 进行比较
import-guard scan . --freeze

# 输出 JSON 格式（适合 CI）
import-guard scan . --format json

# 输出 HTML 报告
import-guard scan . --format html -o report.html --open

# CI 快速检查（有未使用或缺失依赖时返回非 0 退出码）
import-guard check . --strict

# 生成精简的 requirements.txt
import-guard optimize . -o requirements-minimal.txt

# 生成 CI 集成配置
import-guard init --github-action --pre-commit
```

## 项目架构

```
import_guard/
├── scanner/        # AST 扫描器 + import 解析器
├── resolver/       # 包名映射 + PyPI 元数据解析
├── analyzer/       # Diff 引擎 + 未使用/缺失检测
├── reporter/       # CLI / JSON / HTML 报告
├── optimizer/      # Requirements 构建 + 体积预估
├── integrations/   # GitHub Action / Pre-commit / Docker
└── cli.py          # CLI 入口
```

## 开源许可

本项目采用 [MIT License](https://opensource.org/licenses/MIT) 开源协议。

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

## 参与贡献

欢迎提交 Issue 和 Pull Request。请确保您的代码通过 `import-guard check . --strict` 检查 😄

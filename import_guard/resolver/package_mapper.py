"""包名映射器 — 将 import 模块名映射到 PyPI 包名。

大多数情况下模块名 == 包名，但有许多例外：
- import PIL  → 包名是 Pillow
- import yaml  → 包名是 PyYAML
- import cv2   → 包名是 opencv-python
- import bs4   → 包名是 beautifulsoup4
"""

from typing import Dict, Optional

# Known mapping of import names → PyPI package names
IMPORT_TO_PACKAGE: Dict[str, str] = {
    "PIL": "Pillow",
    "pil": "Pillow",
    "yaml": "PyYAML",
    "cv2": "opencv-python",
    "bs4": "beautifulsoup4",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "scipy": "scipy",
    "dateutil": "python-dateutil",
    "googleapiclient": "google-api-python-client",
    "google.cloud": "google-cloud",
    "pkg_resources": "setuptools",
    "IPython": "ipython",
    "jupyter": "jupyter",
    "notebook": "notebook",
    "Crypto": "pycryptodome",
    "Cryptodome": "pycryptodomex",
    "lxml": "lxml",
    "psycopg2": "psycopg2-binary",
    "MySQLdb": "mysqlclient",
    "pymongo": "pymongo",
    "redis": "redis",
    "flask": "Flask",
    "django": "Django",
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "sqlalchemy": "SQLAlchemy",
    "pandas": "pandas",
    "numpy": "numpy",
    "tensorflow": "tensorflow",
    "torch": "torch",
    "transformers": "transformers",
    "matplotlib": "matplotlib",
    "seaborn": "seaborn",
    "plotly": "plotly",
    "click": "click",
    "rich": "rich",
    "typer": "typer",
    "pydantic": "pydantic",
    "celery": "celery",
    "gunicorn": "gunicorn",
    "aiohttp": "aiohttp",
    "httpx": "httpx",
    "boto3": "boto3",
    "botocore": "botocore",
    "grpc": "grpcio",
    "protobuf": "protobuf",
    "dotenv": "python-dotenv",
    "slugify": "python-slugify",
    "decouple": "python-decouple",
    "PIL.Image": "Pillow",
    "PIL.ImageDraw": "Pillow",
    "PIL.ImageFont": "Pillow",
    "PIL.ImageFilter": "Pillow",
}

# Reverse: package → typical import name (for display purposes)
PACKAGE_TO_IMPORT: Dict[str, str] = {v: k for k, v in IMPORT_TO_PACKAGE.items()}


def import_to_package(module_name: str) -> str:
    """Map an import module name to the likely PyPI package name."""
    return IMPORT_TO_PACKAGE.get(module_name, module_name)


def package_to_import(package_name: str) -> Optional[str]:
    """Given a PyPI package name, return its typical import name (if known)."""
    return PACKAGE_TO_IMPORT.get(package_name)


def batch_map_imports(modules: set) -> Dict[str, str]:
    """Map a set of import module names to PyPI package names."""
    return {m: import_to_package(m) for m in modules}

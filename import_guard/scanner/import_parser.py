"""Import 解析器 — 归一化 import 语句，分类为标准库 / 第三方 / 本地。"""

import sys
import sysconfig
from typing import Dict, FrozenSet, Set

# Standard library module names for the current Python version.
# We use sys.builtin_module_names + stdlib module list for completeness.
_STDLIB_BUILTINS: FrozenSet[str] = frozenset(sys.builtin_module_names)

# Known stdlib packages not in builtins
_STDLIB_TOP_LEVEL: FrozenSet[str] = frozenset({
    "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
    "asyncore", "atexit", "audioop", "base64", "bdb", "binascii", "binhex",
    "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb", "chunk",
    "cmath", "cmd", "code", "codecs", "codeop", "collections", "colorsys",
    "compileall", "concurrent", "configparser", "contextlib", "contextvars",
    "copy", "copyreg", "cProfile", "crypt", "csv", "ctypes", "curses",
    "dataclasses", "datetime", "dbm", "decimal", "difflib", "dis",
    "distutils", "doctest", "email", "encodings", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "formatter",
    "fractions", "ftplib", "functools", "gc", "getopt", "getpass",
    "gettext", "glob", "graphlib", "grp", "gzip", "hashlib", "heapq",
    "hmac", "html", "http", "idlelib", "imaplib", "imghdr", "imp",
    "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "lib2to3", "linecache", "locale", "logging", "lzma",
    "mailbox", "mailcap", "marshal", "math", "mimetypes", "mmap",
    "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
    "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
    "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
    "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
    "pydoc", "queue", "quopri", "random", "re", "readline",
    "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets",
    "select", "selectors", "shelve", "shlex", "shutil", "signal",
    "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "sqlite3", "ssl", "stat", "statistics", "string", "stringprep",
    "struct", "subprocess", "sunau", "symtable", "sys", "sysconfig",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test",
    "textwrap", "threading", "time", "timeit", "tkinter", "token",
    "tokenize", "trace", "traceback", "tracemalloc", "tty", "turtle",
    "turtledemo", "types", "typing", "unicodedata", "unittest", "urllib",
    "uu", "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
    "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
    "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
})


class ImportClassifier:
    """Categorize imports as stdlib, third-party, or unknown."""

    def __init__(self):
        self._stdlib = _STDLIB_BUILTINS | _STDLIB_TOP_LEVEL

    def is_stdlib(self, module_name: str) -> bool:
        """Return True if the top-level module is part of the standard library."""
        return module_name in self._stdlib

    def classify(self, imports: Set[str]) -> Dict[str, Set[str]]:
        """Split a set of top-level import names into categories.

        Returns:
            {"stdlib": ..., "third_party": ..., "unknown": ...}
        """
        result = {"stdlib": set(), "third_party": set(), "unknown": set()}
        for name in imports:
            if self.is_stdlib(name):
                result["stdlib"].add(name)
            else:
                # Without a full mapping, mark as third_party; unknown for unresolvable
                result["third_party"].add(name)
        return result


def parse_requirements_txt(path: str) -> Set[str]:
    """Read a requirements.txt file and return normalized package names.

    Handles comments, blank lines, and editable installs (-e).
    Strips version specifiers.
    """
    packages: Set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("-e") or line.startswith("--editable"):
                    continue
                if line.startswith("-r") or line.startswith("--requirement"):
                    continue
                if line.startswith("-"):
                    # Other flags like --index-url, --extra-index-url, etc.
                    continue
                # Extract package name before any version specifier
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0] \
                          .split("!=")[0].split("~=")[0].split(">")[0] \
                          .split("<")[0].split("[")[0].strip().lower().replace("_", "-")
                if pkg:
                    packages.add(pkg)
    except FileNotFoundError:
        pass
    return packages


def parse_pip_freeze_output(freeze_text: str) -> Dict[str, str]:
    """Parse pip freeze output into a dict of {package_name: version}.

    Example input:
        requests==2.28.0
        numpy==1.24.0

    Returns:
        {"requests": "2.28.0", "numpy": "1.24.0"}
    """
    result: Dict[str, str] = {}
    for line in freeze_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" in line:
            name, version = line.split("==", 1)
            name = name.strip().lower().replace("_", "-")
            result[name] = version.strip()
    return result

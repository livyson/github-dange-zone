#!/usr/bin/env python3
"""Gera arquivos de snippet em daily/ para commits automáticos."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

# Conteúdos distintos por slot (um por commit quando count > 1)
SNIPPETS = [
    '''# snippet do dia
def hello():
    return "hello"
''',
    '''# snippet do dia
def add(a, b):
    return a + b
''',
    '''# snippet do dia
def double(x):
    return x * 2
''',
    '''# snippet do dia
def is_even(n):
    return n % 2 == 0
''',
    '''# snippet do dia
def clamp(x, lo, hi):
    return max(lo, min(hi, x))
''',
    '''# snippet do dia
def sign(n):
    return (n > 0) - (n < 0)
''',
    '''# snippet do dia
def square(n):
    return n * n
''',
]


def _ci_footer() -> str:
    """No Actions, garante diff vs. main quando o ficheiro já existia igual ao snippet."""
    rid = os.environ.get("GITHUB_RUN_ID")
    if not rid:
        return ""
    sha = os.environ.get("GITHUB_SHA", "")[:7]
    extra = f" sha={sha}" if sha else ""
    return f"\n\n# ci: workflow_run={rid}{extra}\n"


def main() -> None:
    p = argparse.ArgumentParser(description="Gera arquivos daily/YYYY_MM_DD_NNN.py")
    p.add_argument(
        "--count",
        type=int,
        default=int(os.environ.get("COMMITS_PER_DAY", "7")),
        help="Quantidade de arquivos (commits) para hoje (default: 7 ou COMMITS_PER_DAY)",
    )
    args = p.parse_args()
    if args.count < 1:
        raise SystemExit("--count deve ser >= 1")

    now = datetime.now(timezone.utc)
    prefix = now.strftime("%Y_%m_%d")
    os.makedirs("daily", exist_ok=True)

    for i in range(1, args.count + 1):
        idx = f"{i:03d}"
        path = os.path.join("daily", f"{prefix}_{idx}.py")
        body = SNIPPETS[(i - 1) % len(SNIPPETS)] + _ci_footer()
        with open(path, "w", encoding="utf-8") as f:
            f.write(body)

    print(f"Gerados {args.count} arquivo(s) com prefixo {prefix}_*.py")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Um commit por dia nos três meses civis completos antes do mês atual (datas retroativas)."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


def minus_months(year: int, month: int, n: int) -> tuple[int, int]:
    m = month - n
    y = year
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def iter_days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    today = date.today()
    first_this = date(today.year, today.month, 1)
    y, m = minus_months(today.year, today.month, 3)
    start = date(y, m, 1)
    end = first_this - timedelta(days=1)

    if start > end:
        print("Intervalo vazio; nada a fazer.", file=sys.stderr)
        sys.exit(0)

    log_path = repo_root / "contrib" / "backfill_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rel = log_path.relative_to(repo_root)

    count = 0
    for d in iter_days(start, end):
        iso = d.isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{iso}\n")
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = f"{iso}T12:00:00"
        env["GIT_COMMITTER_DATE"] = f"{iso}T12:00:00"
        subprocess.run(["git", "add", str(rel)], check=True, env=env)
        subprocess.run(
            ["git", "commit", "-m", f"chore: contrib retroativa {iso}"],
            check=True,
            env=env,
        )
        count += 1
        print(iso)

    print(f"Concluído: {start} → {end} ({count} commits)")


if __name__ == "__main__":
    main()

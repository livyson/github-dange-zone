#!/usr/bin/env python3
"""Commits retroativos (1/dia) para preencher o gráfico do GitHub.

Por defeito: N meses civis completos antes do mês atual (--months, default 4).
Com --start e --end usa um intervalo explícito (ISO YYYY-MM-DD).

Ignora dias que já constam em contrib/backfill_log.txt para não duplicar.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def minus_months(year: int, month: int, n: int) -> tuple[int, int]:
    m = month - n
    y = year
    while m <= 0:
        m += 12
        y -= 1
    return y, m


def parse_iso(d: str) -> date:
    if not ISO_DATE.match(d):
        raise argparse.ArgumentTypeError(f"Data inválida: {d} (use YYYY-MM-DD)")
    return datetime.strptime(d, "%Y-%m-%d").date()


def iter_days(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def load_existing_dates(log_path: Path) -> set[str]:
    if not log_path.exists():
        return set()
    out: set[str] = set()
    for line in log_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if ISO_DATE.match(s):
            out.add(s)
    return out


def resolve_range(args: argparse.Namespace, today: date) -> tuple[date, date]:
    if args.start is not None or args.end is not None:
        if args.start is None or args.end is None:
            raise SystemExit("Use --start e --end em conjunto.")
        if args.start > args.end:
            raise SystemExit("--start não pode ser depois de --end.")
        return args.start, args.end

    first_this = date(today.year, today.month, 1)
    y, m = minus_months(today.year, today.month, args.months)
    start = date(y, m, 1)
    end = first_this - timedelta(days=1)
    return start, end


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--months",
        type=int,
        default=4,
        metavar="N",
        help="Meses civis completos antes do mês atual (default: 4; em maio cobre jan–abr)",
    )
    p.add_argument("--start", type=parse_iso, metavar="YYYY-MM-DD", help="Início inclusivo")
    p.add_argument("--end", type=parse_iso, metavar="YYYY-MM-DD", help="Fim inclusivo")
    args = p.parse_args()

    if args.months < 1:
        raise SystemExit("--months deve ser >= 1")

    repo_root = Path(__file__).resolve().parent.parent
    os.chdir(repo_root)
    today = date.today()
    start, end = resolve_range(args, today)

    if start > end:
        print("Intervalo vazio; nada a fazer.", file=sys.stderr)
        sys.exit(0)

    log_path = repo_root / "contrib" / "backfill_log.txt"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    rel = log_path.relative_to(repo_root)
    existing = load_existing_dates(log_path)

    count = 0
    skipped = 0
    for d in iter_days(start, end):
        iso = d.isoformat()
        if iso in existing:
            skipped += 1
            continue
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{iso}\n")
        existing.add(iso)
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

    print(f"Concluído: {start} → {end} | novos={count} | ignorados (já no log)={skipped}")


if __name__ == "__main__":
    main()

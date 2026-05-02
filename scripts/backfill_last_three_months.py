#!/usr/bin/env python3
"""Commits retroativos para preencher o gráfico do GitHub com intensidade variável.

Por defeito: N meses civis completos antes do mês atual (--months, default 4).
Com --start e --end usa um intervalo explícito (ISO YYYY-MM-DD).

Alterna dias \"leves\" (--light commits) e \"pesados\" (--heavy commits) para
tons mais claros e mais escuros no mapa de contribuições.

Cada linha em contrib/backfill_log.txt corresponde a um commit: \"YYYY-MM-DD #n\".
Linhas antigas só com a data (sem \" #\") contam como um commit desse dia.
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


def commits_already_logged(log_path: Path, iso: str) -> int:
    """Quantos commits deste dia já estão representados no log."""
    if not log_path.exists():
        return 0
    pat_num = re.compile(rf"^{re.escape(iso)} #(\d+)$")
    n = 0
    for line in log_path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if ISO_DATE.match(s):
            if s == iso:
                n += 1
            continue
        if pat_num.match(s):
            n += 1
    return n


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
        help="Meses civis completos antes do mês atual (default: 4)",
    )
    p.add_argument("--start", type=parse_iso, metavar="YYYY-MM-DD", help="Início inclusivo")
    p.add_argument("--end", type=parse_iso, metavar="YYYY-MM-DD", help="Fim inclusivo")
    p.add_argument(
        "--light",
        type=int,
        default=1,
        metavar="N",
        help="Commits por dia \"claro\" (default: 1)",
    )
    p.add_argument(
        "--heavy",
        type=int,
        default=10,
        metavar="N",
        help="Commits por dia \"escuro\" (default: 10)",
    )
    p.add_argument(
        "--first-heavy",
        action="store_true",
        help="Começar pelo dia pesado (default: primeiro dia é leve)",
    )
    args = p.parse_args()

    if args.months < 1:
        raise SystemExit("--months deve ser >= 1")
    if args.light < 1 or args.heavy < 1:
        raise SystemExit("--light e --heavy devem ser >= 1")
    if args.heavy <= args.light:
        raise SystemExit("--heavy deve ser maior que --light para haver contraste no gráfico")

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

    commits_new = 0
    days_skipped = 0
    day_index = 0
    for d in iter_days(start, end):
        iso = d.isoformat()
        heavy_day = (day_index % 2 == 1) if not args.first_heavy else (day_index % 2 == 0)
        want = args.heavy if heavy_day else args.light
        have = commits_already_logged(log_path, iso)

        if have >= want:
            days_skipped += 1
            day_index += 1
            continue

        env_date = os.environ.copy()
        env_date["GIT_AUTHOR_DATE"] = f"{iso}T12:00:00"
        env_date["GIT_COMMITTER_DATE"] = f"{iso}T12:00:00"

        for k in range(have + 1, want + 1):
            line = f"{iso} #{k}\n"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
            subprocess.run(["git", "add", str(rel)], check=True, env=env_date)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"chore: contrib retroativa {iso} ({k}/{want})",
                ],
                check=True,
                env=env_date,
            )
            commits_new += 1
            tag = "pesado" if heavy_day else "leve"
            print(f"{iso} #{k}/{want} ({tag})")

        day_index += 1

    print(
        f"Concluído: {start} → {end} | commits novos={commits_new} | dias já completos={days_skipped}"
    )


if __name__ == "__main__":
    main()

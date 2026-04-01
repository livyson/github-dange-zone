# Instala dependências (nenhuma além do Python padrão)
python3 --version  # precisa ser 3.8+

# Simula primeiro (--dry-run)
# python3 backfill.py --start 2025-03-01 --end 2025-12-31 --dry-run

# Executa de verdade
python3 backfill.py --start 2025-03-01 --end 2025-12-31

# Com mais commits por dia (gráfico mais escuro)
python3 backfill.py --start 2026-04-01 --end 2027-04-01 --commits-per-day 2
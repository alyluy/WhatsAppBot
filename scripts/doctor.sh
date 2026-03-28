#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ok() { echo "[OK] $1"; }
warn() { echo "[WARN] $1"; }
err() { echo "[ERR] $1"; }

EXIT_CODE=0

echo "Проверка окружения проекта WhatsAppBot"

echo "1) ОС"
if [[ "$(uname -s)" = "Darwin" ]]; then
  ok "macOS обнаружена"
else
  warn "Скрипты bootstrap рассчитаны на macOS"
fi

echo "2) Python"
if command -v python3 >/dev/null 2>&1; then
  ok "$(python3 --version)"
else
  err "python3 не найден"
  EXIT_CODE=1
fi

echo "3) Homebrew"
if command -v brew >/dev/null 2>&1; then
  ok "brew найден"
else
  warn "brew не найден (bootstrap попытается установить)"
fi

echo "4) PostgreSQL"
if command -v psql >/dev/null 2>&1; then
  ok "$(psql --version)"
  if command -v pg_isready >/dev/null 2>&1 && pg_isready -q; then
    ok "PostgreSQL отвечает"
  else
    warn "PostgreSQL не отвечает (bootstrap попытается запустить)"
  fi
else
  warn "psql не найден (bootstrap установит postgresql@16)"
fi

echo "5) Chrome"
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ -x "$CHROME_BIN" ]; then
  ok "$("$CHROME_BIN" --version)"
else
  warn "Google Chrome не найден в /Applications"
fi

echo "6) ChromeDriver"
DRIVER_PATH=""
if command -v chromedriver >/dev/null 2>&1; then
  DRIVER_PATH="$(command -v chromedriver)"
else
  DRIVER_PATH="$(find /opt/homebrew /usr/local -name chromedriver 2>/dev/null | head -n 1 || true)"
  if [ -z "$DRIVER_PATH" ] && [ -x "/Applications/Chromedriver.app/Contents/MacOS/chromedriver" ]; then
    DRIVER_PATH="/Applications/Chromedriver.app/Contents/MacOS/chromedriver"
  fi
fi

if [ -n "$DRIVER_PATH" ] && [ -x "$DRIVER_PATH" ]; then
  ok "chromedriver: $DRIVER_PATH"
  ok "$("$DRIVER_PATH" --version)"
else
  warn "chromedriver не найден"
fi

echo "7) .env"
if [ -f .env ]; then
  ok ".env найден"
else
  warn ".env отсутствует (будет создан из .env.example)"
fi

echo "8) Рекомендованный запуск"
echo "LOCAL_WA_DEFAULT_CHAT='wbot_test' ./scripts/bootstrap.sh"

if [ "$EXIT_CODE" -ne 0 ]; then
  exit "$EXIT_CODE"
fi

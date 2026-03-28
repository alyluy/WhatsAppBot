#!/usr/bin/env bash
set -euo pipefail
trap 'echo "[ОШИБКА] bootstrap.sh: строка $LINENO: команда \"$BASH_COMMAND\" завершилась с ошибкой."' ERR

if [ "${BOOTSTRAP_DEBUG:-0}" = "1" ]; then
  set -x
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Скрипт рассчитан на macOS."
  echo "Для Linux используйте scripts/setup_python_env.sh и scripts/setup_local.sh вручную."
  exit 1
fi

if [ -z "${LOCAL_WA_DEFAULT_CHAT:-}" ]; then
  echo "Введите имя чата WhatsApp, куда бот будет отправлять ответы:"
  read -r LOCAL_WA_DEFAULT_CHAT
fi

if [ -z "$LOCAL_WA_DEFAULT_CHAT" ]; then
  echo "Имя чата пустое. Остановлено."
  exit 1
fi

echo "[1/3] Установка системных компонентов"
./scripts/install_macos_components.sh

if [ -z "${LOCAL_WA_CHROMEDRIVER_PATH:-}" ]; then
  if command -v chromedriver >/dev/null 2>&1; then
    LOCAL_WA_CHROMEDRIVER_PATH="$(command -v chromedriver)"
  else
    LOCAL_WA_CHROMEDRIVER_PATH="$(find /opt/homebrew /usr/local -name chromedriver 2>/dev/null | head -n 1 || true)"
    if [ -z "$LOCAL_WA_CHROMEDRIVER_PATH" ] && [ -x "/Applications/Chromedriver.app/Contents/MacOS/chromedriver" ]; then
      LOCAL_WA_CHROMEDRIVER_PATH="/Applications/Chromedriver.app/Contents/MacOS/chromedriver"
    fi
  fi
fi

echo "[2/3] Настройка проекта и локальной БД"
LOCAL_WA_DEFAULT_CHAT="$LOCAL_WA_DEFAULT_CHAT" \
LOCAL_WA_CHROMEDRIVER_PATH="${LOCAL_WA_CHROMEDRIVER_PATH:-}" \
LOCAL_DB_NAME="${LOCAL_DB_NAME:-whatsapp_bot}" \
LOCAL_DB_USER="${LOCAL_DB_USER:-wbot_user}" \
LOCAL_DB_PASSWORD="${LOCAL_DB_PASSWORD:-StrongPass123!}" \
LOCAL_APP_USER="${LOCAL_APP_USER:-user1}" \
./scripts/setup_local.sh

echo "[3/3] Финальный запуск"
echo "Откроется WhatsApp Web, при первом запуске нужно отсканировать QR-код."
source .venv/bin/activate
python main.py

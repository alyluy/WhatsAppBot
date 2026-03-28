#!/usr/bin/env bash
set -euo pipefail
trap 'echo "[ОШИБКА] setup_local.sh: строка $LINENO: команда \"$BASH_COMMAND\" завершилась с ошибкой."' ERR

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DB_NAME="${LOCAL_DB_NAME:-whatsapp_bot}"
DB_USER="${LOCAL_DB_USER:-wbot_user}"
DB_PASSWORD="${LOCAL_DB_PASSWORD:-StrongPass123!}"
APP_USER_VALUE="${LOCAL_APP_USER:-user1}"
WA_CHAT_VALUE="${LOCAL_WA_DEFAULT_CHAT:-}"
WA_PROFILE_VALUE="${LOCAL_WA_PROFILE_DIR:-$PROJECT_ROOT/.wa_profile}"
WA_DRIVER_VALUE="${LOCAL_WA_CHROMEDRIVER_PATH:-}"
WA_DRIVER_VERSION_VALUE=""

# Универсальный upsert переменной в .env
upsert_env() {
  local key="$1"
  local value="$2"
  local env_file="$3"

  if grep -qE "^${key}=" "$env_file"; then
    sed -i '' "s|^${key}=.*|${key}=${value}|" "$env_file"
  else
    printf '%s=%s\n' "$key" "$value" >> "$env_file"
  fi
}

# Экранирование одинарных кавычек для SQL-строк
sql_escape() {
  local input="$1"
  printf "%s" "${input//\'/\'\'}"
}

ensure_postgres_started() {
  if command -v pg_isready >/dev/null 2>&1 && pg_isready -q; then
    return 0
  fi

  if command -v brew >/dev/null 2>&1; then
    if brew services list | grep -q 'postgresql@16'; then
      brew services start postgresql@16 >/dev/null 2>&1 || true
    else
      brew services start postgresql >/dev/null 2>&1 || true
    fi
  fi

  if command -v pg_isready >/dev/null 2>&1; then
    for _ in $(seq 1 20); do
      if pg_isready -q; then
        return 0
      fi
      sleep 1
    done
  fi

  echo "Не удалось автоматически поднять PostgreSQL. Запустите его вручную и повторите команду."
  exit 1
}

detect_chromedriver() {
  if [ -n "$WA_DRIVER_VALUE" ] && [ -x "$WA_DRIVER_VALUE" ]; then
    return 0
  fi

  if command -v chromedriver >/dev/null 2>&1; then
    WA_DRIVER_VALUE="$(command -v chromedriver)"
    return 0
  fi

  local detected
  detected="$(find /opt/homebrew /usr/local -name chromedriver 2>/dev/null | head -n 1 || true)"
  if [ -n "$detected" ] && [ -x "$detected" ]; then
    WA_DRIVER_VALUE="$detected"
    return 0
  fi

  local cask_driver="/Applications/Chromedriver.app/Contents/MacOS/chromedriver"
  if [ -x "$cask_driver" ]; then
    WA_DRIVER_VALUE="$cask_driver"
    return 0
  fi

  return 1
}

detect_chromedriver_version() {
  if [ -z "$WA_DRIVER_VALUE" ] || [ ! -x "$WA_DRIVER_VALUE" ]; then
    WA_DRIVER_VERSION_VALUE=""
    return 0
  fi
  WA_DRIVER_VERSION_VALUE="$("$WA_DRIVER_VALUE" --version 2>/dev/null | awk '{print $2}' || true)"
}

setup_database() {
  local escaped_user
  local escaped_password
  local escaped_db

  escaped_user="$(sql_escape "$DB_USER")"
  escaped_password="$(sql_escape "$DB_PASSWORD")"
  escaped_db="$(sql_escape "$DB_NAME")"

  if ! psql postgres -v ON_ERROR_STOP=1 -c "SELECT 1" >/dev/null 2>&1; then
    echo "Нет доступа к локальному PostgreSQL через psql."
    echo "Проверьте, что служба запущена и у текущего пользователя есть доступ."
    echo "Проверка вручную: psql postgres -c 'SELECT 1;'"
    exit 1
  fi

  psql postgres -v ON_ERROR_STOP=1 <<SQL
DO
\$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${escaped_user}') THEN
        CREATE ROLE "${DB_USER}" LOGIN PASSWORD '${escaped_password}';
    ELSE
        ALTER ROLE "${DB_USER}" WITH LOGIN PASSWORD '${escaped_password}';
    END IF;
END
\$\$;
SQL

  if ! psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${escaped_db}'" | grep -q 1; then
    psql postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"
  fi

  psql postgres -v ON_ERROR_STOP=1 <<SQL
GRANT ALL PRIVILEGES ON DATABASE "${DB_NAME}" TO "${DB_USER}";
SQL
}

echo "[1/4] Подготовка Python-окружения"
./scripts/setup_python_env.sh

echo "[2/4] Запуск локального PostgreSQL"
ensure_postgres_started

echo "[3/4] Создание БД и пользователя"
setup_database

if [ ! -f .env ]; then
  cp .env.example .env
fi

mkdir -p "$WA_PROFILE_VALUE"
detect_chromedriver || true
detect_chromedriver_version

echo "[4/4] Настройка .env для локального запуска"
upsert_env "APP_MODE" "whatsapp" .env
upsert_env "APP_USER" "$APP_USER_VALUE" .env
upsert_env "SSH_ENABLED" "false" .env
upsert_env "DB_HOST" "/tmp" .env
upsert_env "DB_PORT" "5432" .env
upsert_env "DB_NAME" "$DB_NAME" .env
upsert_env "DB_USER" "$DB_USER" .env
upsert_env "DB_PASSWORD" "$DB_PASSWORD" .env
upsert_env "DB_GSSENCMODE" "disable" .env
upsert_env "WA_CHROME_USER_DATA_DIR" "$WA_PROFILE_VALUE" .env
upsert_env "WA_DEFAULT_CHAT" "$WA_CHAT_VALUE" .env

if [ -n "$WA_DRIVER_VALUE" ]; then
  upsert_env "WA_CHROMEDRIVER_PATH" "$WA_DRIVER_VALUE" .env
fi
if [ -n "$WA_DRIVER_VERSION_VALUE" ]; then
  upsert_env "WA_CHROMEDRIVER_VERSION" "$WA_DRIVER_VERSION_VALUE" .env
fi

echo "Готово."
echo "Дальше:"
echo "1) Проверьте/дополните WA_DEFAULT_CHAT в .env"
echo "2) Текущий chromedriver: ${WA_DRIVER_VALUE:-не найден}"
echo "3) Версия chromedriver: ${WA_DRIVER_VERSION_VALUE:-не определена}"
echo "4) Если драйвер не найден, запустите scripts/install_macos_components.sh"
echo "5) Запуск: source .venv/bin/activate && python main.py"

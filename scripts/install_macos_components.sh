#!/usr/bin/env bash
set -euo pipefail
trap 'echo "[ОШИБКА] install_macos_components.sh: строка $LINENO: команда \"$BASH_COMMAND\" завершилась с ошибкой."' ERR

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Скрипт поддерживает только macOS."
  exit 1
fi

install_brew() {
  if command -v brew >/dev/null 2>&1; then
    return 0
  fi

  echo "Homebrew не найден. Устанавливаю Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  if [ -x /opt/homebrew/bin/brew ]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi

  if ! command -v brew >/dev/null 2>&1; then
    echo "Не удалось установить Homebrew автоматически."
    exit 1
  fi
}

brew_install_formula_if_missing() {
  local formula="$1"
  if brew list --formula | grep -qx "$formula"; then
    echo "Формула $formula уже установлена"
    return 0
  fi
  brew install "$formula"
}

brew_install_cask_if_missing() {
  local cask="$1"
  if brew list --cask | grep -qx "$cask"; then
    echo "Cask $cask уже установлен"
    return 0
  fi

  # Если приложение уже установлено вручную, не валим bootstrap.
  if [ "$cask" = "google-chrome" ] && [ -d "/Applications/Google Chrome.app" ]; then
    echo "Google Chrome уже установлен в /Applications, пропускаю установку cask"
    return 0
  fi
  if [ "$cask" = "chromedriver" ] && [ -d "/Applications/Chromedriver.app" ]; then
    echo "Chromedriver уже установлен в /Applications, пропускаю установку cask"
    return 0
  fi

  brew install --cask "$cask"
}

start_postgres_service() {
  if brew list --formula | grep -qx "postgresql@16"; then
    brew services start postgresql@16 || true
  elif brew list --formula | grep -qx "postgresql"; then
    brew services start postgresql || true
  fi
}

print_versions() {
  echo "--- Проверка версий ---"

  if command -v python3 >/dev/null 2>&1; then
    python3 --version
  fi

  if command -v psql >/dev/null 2>&1; then
    psql --version
  fi

  if command -v chromedriver >/dev/null 2>&1; then
    chromedriver --version
  else
    local detected
    detected="$(find /opt/homebrew /usr/local -name chromedriver 2>/dev/null | head -n 1 || true)"
    if [ -z "$detected" ] && [ -x "/Applications/Chromedriver.app/Contents/MacOS/chromedriver" ]; then
      detected="/Applications/Chromedriver.app/Contents/MacOS/chromedriver"
    fi
    if [ -n "$detected" ]; then
      "$detected" --version
      echo "chromedriver path: $detected"
    else
      echo "chromedriver не найден"
    fi
  fi

  local chrome_bin="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  if [ -x "$chrome_bin" ]; then
    "$chrome_bin" --version
  else
    echo "Google Chrome не найден в /Applications"
  fi
}

echo "[1/4] Проверка Homebrew"
install_brew

echo "[2/4] Установка компонентов"
brew_install_formula_if_missing postgresql@16
brew_install_cask_if_missing google-chrome
brew_install_cask_if_missing chromedriver

echo "[3/4] Запуск PostgreSQL"
start_postgres_service

echo "[4/4] Контроль версий"
print_versions

echo "Системные компоненты готовы."

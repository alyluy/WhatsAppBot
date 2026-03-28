#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEY_DIR="$PROJECT_ROOT/keys"
KEY_NAME="id_ed25519_whatsappbot"

mkdir -p "$KEY_DIR"

if [ -f "$KEY_DIR/$KEY_NAME" ]; then
  echo "Key already exists: $KEY_DIR/$KEY_NAME"
  exit 0
fi

ssh-keygen -t ed25519 -f "$KEY_DIR/$KEY_NAME" -C "whatsappbot" -N ""

echo "Private key: $KEY_DIR/$KEY_NAME"
echo "Public key:  $KEY_DIR/$KEY_NAME.pub"
echo "Добавьте публичный ключ на сервер в ~/.ssh/authorized_keys"

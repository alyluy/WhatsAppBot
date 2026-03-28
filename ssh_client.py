"""ssh_client.py
Поддержка SSH-туннеля для подключения к удаленному PostgreSQL.
"""

import atexit
import os
import threading
from typing import Optional, Tuple

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder


load_dotenv()

_lock = threading.Lock()
_tunnel: Optional[SSHTunnelForwarder] = None


def _env_bool(name: str, default: bool = False) -> bool:
    """Читает boolean-переменную окружения с дефолтным значением."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_enabled() -> bool:
    """Проверяет, включен ли SSH-туннель в конфигурации."""
    return _env_bool("SSH_ENABLED", False)


def start_tunnel() -> SSHTunnelForwarder:
    """Запускает SSH-туннель, если он еще не активен."""
    global _tunnel

    if not is_enabled():
        raise RuntimeError("SSH tunnel is disabled. Set SSH_ENABLED=true in .env")

    with _lock:
        if _tunnel and _tunnel.is_active:
            return _tunnel

        ssh_host = os.getenv("SSH_HOST")
        ssh_port = int(os.getenv("SSH_PORT", "22"))
        ssh_username = os.getenv("SSH_USERNAME")
        ssh_private_key_path = os.getenv("SSH_PRIVATE_KEY_PATH")
        ssh_passphrase = os.getenv("SSH_PASSPHRASE") or None

        remote_db_host = os.getenv("SSH_REMOTE_DB_HOST", "127.0.0.1")
        remote_db_port = int(os.getenv("SSH_REMOTE_DB_PORT", "5432"))

        local_bind_host = os.getenv("SSH_LOCAL_BIND_HOST", "127.0.0.1")
        local_bind_port = int(os.getenv("SSH_LOCAL_BIND_PORT", "6543"))

        required = {
            "SSH_HOST": ssh_host,
            "SSH_USERNAME": ssh_username,
            "SSH_PRIVATE_KEY_PATH": ssh_private_key_path,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "Missing SSH settings in .env: {}".format(", ".join(missing))
            )

        _tunnel = SSHTunnelForwarder(
            ssh_address_or_host=(ssh_host, ssh_port),
            ssh_username=ssh_username,
            ssh_pkey=ssh_private_key_path,
            ssh_private_key_password=ssh_passphrase,
            remote_bind_address=(remote_db_host, remote_db_port),
            local_bind_address=(local_bind_host, local_bind_port),
        )
        _tunnel.start()
        return _tunnel


def get_tunnel_db_endpoint() -> Tuple[str, int]:
    """Возвращает endpoint локального конца SSH-туннеля."""
    tunnel = start_tunnel()
    return tunnel.local_bind_host, int(tunnel.local_bind_port)


def stop_tunnel() -> None:
    """Останавливает туннель, если он был запущен."""
    global _tunnel

    with _lock:
        if _tunnel:
            try:
                if _tunnel.is_active:
                    _tunnel.stop()
            finally:
                _tunnel = None


atexit.register(stop_tunnel)

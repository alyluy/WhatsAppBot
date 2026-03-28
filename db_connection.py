"""db_connection.py
Управление подключением к PostgreSQL (опционально через SSH-туннель).
"""

import os
from typing import Dict, Tuple

import psycopg2
from dotenv import load_dotenv

import ssh_client


load_dotenv()


def _env_bool(name: str, default: bool = False) -> bool:
    """Читает boolean-переменную окружения с дефолтным значением."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_db_config() -> Dict[str, object]:
    """Считывает конфигурацию БД из переменных окружения."""
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "whatsapp_bot"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
        "gssencmode": os.getenv("DB_GSSENCMODE", "disable"),
    }


def _resolve_db_endpoint() -> Tuple[str, int]:
    """Возвращает хост/порт PostgreSQL, учитывая SSH-туннель."""
    if _env_bool("SSH_ENABLED", False):
        return ssh_client.get_tunnel_db_endpoint()

    config = get_db_config()
    return str(config["host"]), int(config["port"])


def get_connection():
    """Создает и возвращает новое подключение к PostgreSQL."""
    config = get_db_config()
    db_host, db_port = _resolve_db_endpoint()

    connection = psycopg2.connect(
        host=db_host,
        port=db_port,
        dbname=config["dbname"],
        user=config["user"],
        password=config["password"],
        connect_timeout=config["connect_timeout"],
        gssencmode=config["gssencmode"],
    )
    connection.autocommit = False
    return connection


def check_connection() -> bool:
    """Проверяет доступность подключения к БД."""
    connection = None
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    finally:
        if connection:
            connection.close()


def init_schema() -> None:
    """Создает таблицы и стартовые данные при первом запуске."""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    question_count INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    message_text TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS logs (
                    id BIGSERIAL PRIMARY KEY,
                    log_message TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                )
                """
            )

            default_users = [
                ("admin", "Admin"),
                ("user1", "User"),
                ("guest", "Guest"),
            ]
            for username, role in default_users:
                cursor.execute(
                    """
                    INSERT INTO users (username, role, question_count)
                    VALUES (%s, %s, 0)
                    ON CONFLICT (username) DO NOTHING
                    """,
                    (username, role),
                )

        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

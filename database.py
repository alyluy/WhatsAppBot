"""database.py
SQL-слой для работы с PostgreSQL.
"""

from typing import Dict, List, Optional

import db_connection


_initialized = False


def initialize() -> None:
    """Инициализирует схему БД и стартовые данные."""
    global _initialized
    if _initialized:
        return
    db_connection.init_schema()
    _initialized = True


def _ensure_initialized() -> None:
    """Гарантирует, что схема БД инициализирована перед операцией."""
    if not _initialized:
        initialize()


def add_log(message: str) -> None:
    """Добавляет запись в таблицу логов."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO logs (log_message) VALUES (%s)",
                (message,),
            )
        connection.commit()
        print(f"[LOG]: {message}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_logs(limit: int = 200) -> List[str]:
    """Возвращает последние записи лога в хронологическом порядке."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT log_message, created_at
                FROM logs
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        rows.reverse()
        return [f"[{created_at}] {message}" for message, created_at in rows]
    finally:
        connection.close()


def get_user(username: str) -> Optional[Dict[str, object]]:
    """Возвращает данные пользователя по его имени."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, role, question_count
                FROM users
                WHERE username = %s
                """,
                (username,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return {
            "username": row[0],
            "role": row[1],
            "question_count": row[2],
        }
    finally:
        connection.close()


def ensure_user(username: str, default_role: str = "Guest") -> None:
    """Создает пользователя, если его еще нет в таблице."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, role, question_count)
                VALUES (%s, %s, 0)
                ON CONFLICT (username) DO NOTHING
                """,
                (username, default_role),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def update_user_role(username: str, new_role: str) -> None:
    """Обновляет роль пользователя и пишет событие в лог."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET role = %s, updated_at = NOW()
                WHERE username = %s
                """,
                (new_role, username),
            )
        connection.commit()
        add_log(f"Роль пользователя {username} изменена на {new_role}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def increment_question_count(username: str) -> int:
    """Увеличивает счетчик вопросов пользователя и возвращает новое значение."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET question_count = question_count + 1,
                    updated_at = NOW()
                WHERE username = %s
                RETURNING question_count
                """,
                (username,),
            )
            row = cursor.fetchone()
        connection.commit()
        return int(row[0]) if row else 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def reset_question_count(username: str) -> int:
    """Сбрасывает счетчик вопросов пользователя и возвращает новое значение."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET question_count = 0,
                    updated_at = NOW()
                WHERE username = %s
                RETURNING question_count
                """,
                (username,),
            )
            row = cursor.fetchone()
        connection.commit()
        return int(row[0]) if row else 0
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def add_message(message: str) -> None:
    """Добавляет новое сообщение в таблицу messages."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO messages (message_text) VALUES (%s)",
                (message,),
            )
        connection.commit()
        add_log(f"Сообщение добавлено: {message}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def get_all_messages() -> List[str]:
    """Возвращает все сообщения в порядке их создания."""
    _ensure_initialized()
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT message_text
                FROM messages
                ORDER BY id ASC
                """
            )
            rows = cursor.fetchall()
        return [row[0] for row in rows]
    finally:
        connection.close()


def _get_message_row_by_index(index: int):
    """Возвращает строку сообщения по порядковому индексу в списке."""
    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, message_text
                FROM messages
                ORDER BY id ASC
                LIMIT 1 OFFSET %s
                """,
                (index,),
            )
            return cursor.fetchone()
    finally:
        connection.close()


def update_message(index: int, new_message: str) -> bool:
    """Обновляет сообщение по индексу; возвращает успех операции."""
    _ensure_initialized()
    row = _get_message_row_by_index(index)
    if not row:
        add_log(f"Ошибка обновления: сообщение с index={index} не найдено")
        return False

    message_id, old_message = row

    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE messages
                SET message_text = %s,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (new_message, message_id),
            )
        connection.commit()
        add_log(f"Сообщение обновлено: {old_message} -> {new_message}")
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def delete_message(index: int) -> bool:
    """Удаляет сообщение по индексу; возвращает успех операции."""
    _ensure_initialized()
    row = _get_message_row_by_index(index)
    if not row:
        add_log(f"Ошибка удаления: сообщение с index={index} не найдено")
        return False

    message_id, removed_message = row

    connection = db_connection.get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM messages WHERE id = %s",
                (message_id,),
            )
        connection.commit()
        add_log(f"Сообщение удалено: {removed_message}")
        return True
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

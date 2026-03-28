# crudl.py
# Модуль реализации операций CRUDL

from constants import *
import roles


def create_message(username, message, db):
    """Создает сообщение."""
    role = roles.get_user_role(username, db)

    if not roles.has_permission(role, CREATE):
        db.add_log(f"Доступ запрещен: {username} не может создавать сообщения")
        return False

    db.add_message(f"{username}: {message}")
    return True


def read_messages(username, db):
    """Возвращает сообщения."""
    role = roles.get_user_role(username, db)

    if not roles.has_permission(role, READ):
        db.add_log(f"Доступ запрещен: {username} не может читать сообщения")
        return []

    return db.get_all_messages()


def update_message(username, index, new_message, db):
    """Обновляет сообщение."""
    role = roles.get_user_role(username, db)

    if not roles.has_permission(role, UPDATE):
        db.add_log(f"Доступ запрещен: {username} не может изменять сообщения")
        return False

    return db.update_message(index, f"{username}: {new_message}")


def delete_message(username, index, db):
    """Удаляет сообщение."""
    role = roles.get_user_role(username, db)

    if not roles.has_permission(role, DELETE):
        db.add_log(f"Доступ запрещен: {username} не может удалять сообщения")
        return False

    return db.delete_message(index)


def list_data(username, db):
    """Возвращает список данных."""
    role = roles.get_user_role(username, db)

    if not roles.has_permission(role, LIST):
        db.add_log(f"Доступ запрещен: {username} не может получать список данных")
        return {}

    return {
        "messages": db.get_all_messages(),
        "logs": db.get_logs(),
    }

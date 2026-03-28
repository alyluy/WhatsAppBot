# roles.py
# Модуль управления ролями и правами доступа

from constants import *


ROLES_PERMISSIONS = {
    ROLE_GUEST: [READ, LIST],
    ROLE_USER: [READ, DELETE, LIST],
    ROLE_IGN_USER: [LIST],
    ROLE_ADMIN: [CREATE, READ, UPDATE, DELETE, LIST],
}


def has_permission(role, operation):
    """Проверяет право роли на выполнение операции."""
    return operation in ROLES_PERMISSIONS.get(role, [])


def check_and_update_role(username, message, db):
    """Проверяет условия смены роли пользователя."""
    user = db.get_user(username)

    if not user:
        return

    if "?" in message:
        question_count = db.increment_question_count(username)
    else:
        question_count = db.reset_question_count(username)

    if question_count >= 3 and user["role"] != ROLE_IGN_USER:
        db.update_user_role(username, ROLE_IGN_USER)


def get_user_role(username, db):
    """Возвращает роль пользователя."""
    user = db.get_user(username)
    if user:
        return user["role"]
    return None

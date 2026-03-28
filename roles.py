# roles.py
# Модуль управления ролями и правами доступа

from constants import *

# ===== Описание ролей и прав =====

ROLES_PERMISSIONS = {
    ROLE_GUEST: [READ, LIST],
    ROLE_USER: [READ, DELETE, LIST],
    ROLE_IGN_USER: [LIST],
    ROLE_ADMIN: [CREATE, READ, UPDATE, DELETE, LIST]
}

# ===== Проверка прав доступа =====

def has_permission(role, operation):
    """Проверяет право роли на выполнение операции."""
    return operation in ROLES_PERMISSIONS.get(role, [])

# ===== Логика смены роли =====

def check_and_update_role(username, message, db):
    """Проверяет условия смены роли пользователя."""
    user = db.get_user(username)

    if not user:
        return

    # Проверяем, есть ли вопросительный знак
    if "?" in message:
        db.increment_question_count(username)
    else:
        db.reset_question_count(username)

    # Если 3 вопроса подряд → IgnUser
    if user["question_count"] >= 3 and user["role"] != ROLE_IGN_USER:
        db.update_user_role(username, ROLE_IGN_USER)

# ===== Получение роли пользователя =====

def get_user_role(username, db):
    """Возвращает роль пользователя."""
    user = db.get_user(username)
    if user:
        return user["role"]
    return None
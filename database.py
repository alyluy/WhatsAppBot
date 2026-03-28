# database.py
# Модуль эмуляции базы данных

# ===== Эмуляция SSH =====

VALID_SSH_KEY = "valid_ssh_key"

def check_ssh_access(ssh_key):
    """Проверяет корректность SSH-ключа."""
    return ssh_key == VALID_SSH_KEY

# ===== "База данных" =====

messages_db = []

users_db = {
    "admin": {"role": "Admin", "question_count": 0},
    "user1": {"role": "User", "question_count": 0},
    "guest": {"role": "Guest", "question_count": 0}
}

logs_db = []

# ===== Работа с логами =====

def add_log(message):
    """Добавляет запись в лог системы."""
    logs_db.append(message)
    print(f"[LOG]: {message}")

# ===== Работа с пользователями =====

def get_user(username):
    """Возвращает пользователя по имени."""
    return users_db.get(username)

def update_user_role(username, new_role):
    """Обновляет роль пользователя."""
    if username in users_db:
        users_db[username]["role"] = new_role
        add_log(f"Роль пользователя {username} изменена на {new_role}")

def increment_question_count(username):
    """Увеличивает счетчик вопросов."""
    if username in users_db:
        users_db[username]["question_count"] += 1

def reset_question_count(username):
    """Сбрасывает счетчик вопросов."""
    if username in users_db:
        users_db[username]["question_count"] = 0

# ===== Работа с сообщениями =====

def add_message(message):
    """Добавляет сообщение в базу."""
    messages_db.append(message)
    add_log(f"Сообщение добавлено: {message}")

def get_all_messages():
    """Возвращает все сообщения."""
    return messages_db

def update_message(index, new_message):
    """Обновляет сообщение по индексу."""
    if 0 <= index < len(messages_db):
        old = messages_db[index]
        messages_db[index] = new_message
        add_log(f"Сообщение обновлено: {old} -> {new_message}")

def delete_message(index):
    """Удаляет сообщение по индексу."""
    if 0 <= index < len(messages_db):
        removed = messages_db.pop(index)
        add_log(f"Сообщение удалено: {removed}")

def get_logs():
    """Возвращает лог системы."""
    return logs_db
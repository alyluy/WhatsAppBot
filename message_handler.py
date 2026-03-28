# message_handler.py
# Модуль обработки сообщений пользователя

from constants import *
import crudl
import roles

# ===== Обработка сообщения =====

def handle_message(username, message, db):
    """Обрабатывает сообщение пользователя."""
    # Логируем входящее сообщение
    db.add_log(f"{username} отправил сообщение: {message}")

    # Проверяем и обновляем роль
    roles.check_and_update_role(username, message, db)

    # Получаем актуальную роль
    role = roles.get_user_role(username, db)

    # ===== Определение команды =====

    # CREATE
    if message.startswith("create "):
        text = message.replace("create ", "", 1)
        crudl.create_message(username, text, db)
        return "Сообщение создано"

    # READ
    if message == "read":
        messages = crudl.read_messages(username, db)
        return messages

    # UPDATE
    if message.startswith("update "):
        try:
            parts = message.split(" ", 2)
            index = int(parts[1])
            new_text = parts[2]
            crudl.update_message(username, index, new_text, db)
            return "Сообщение обновлено"
        except:
            return "Ошибка формата команды update"

    # DELETE
    if message.startswith("delete "):
        try:
            index = int(message.split(" ")[1])
            crudl.delete_message(username, index, db)
            return "Сообщение удалено"
        except:
            return "Ошибка формата команды delete"

    # LIST
    if message == "list":
        data = crudl.list_data(username, db)
        return data

    # ===== Если команда не распознана =====

    return f"Неизвестная команда. Ваша роль: {role}"
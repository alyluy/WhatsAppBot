# message_handler.py
# Модуль обработки сообщений пользователя

import crudl
import roles


def _normalize_response_payload(payload):
    """Унифицирует вывод для каналов (console/WhatsApp)."""
    if isinstance(payload, list):
        if not payload:
            return "Сообщений нет"
        return "\n".join(str(item) for item in payload)

    if isinstance(payload, dict):
        messages = payload.get("messages", [])
        logs = payload.get("logs", [])
        return (
            "Messages:\n"
            + ("\n".join(messages) if messages else "<empty>")
            + "\n\nLogs:\n"
            + ("\n".join(logs) if logs else "<empty>")
        )

    return str(payload)


def handle_message(username, message, db):
    """Обрабатывает сообщение пользователя."""
    db.ensure_user(username)
    db.add_log(f"{username} отправил сообщение: {message}")

    roles.check_and_update_role(username, message, db)
    role = roles.get_user_role(username, db)

    if message.startswith("create "):
        text = message.replace("create ", "", 1)
        ok = crudl.create_message(username, text, db)
        return "Сообщение создано" if ok else "Нет прав на Create"

    if message == "read":
        messages = crudl.read_messages(username, db)
        return _normalize_response_payload(messages)

    if message.startswith("update "):
        try:
            parts = message.split(" ", 2)
            index = int(parts[1])
            new_text = parts[2]
            ok = crudl.update_message(username, index, new_text, db)
            return "Сообщение обновлено" if ok else "Не удалось обновить сообщение"
        except Exception:
            return "Ошибка формата команды update"

    if message.startswith("delete "):
        try:
            index = int(message.split(" ")[1])
            ok = crudl.delete_message(username, index, db)
            return "Сообщение удалено" if ok else "Не удалось удалить сообщение"
        except Exception:
            return "Ошибка формата команды delete"

    if message == "list":
        data = crudl.list_data(username, db)
        return _normalize_response_payload(data)

    return f"Неизвестная команда. Ваша роль: {role}"

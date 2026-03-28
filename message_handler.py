# message_handler.py
# Модуль обработки сообщений пользователя.

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import roles
from storage_bridge import CrudlBridge, DatabaseStorageImplementor


@dataclass
class CommandRequest:
    """DTO запроса команды для цепочки обработчиков."""

    username: str
    message: str


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


class BaseCommandHandler(ABC):
    """Базовый элемент цепочки обработчиков (Chain of Responsibility)."""

    def __init__(self, crudl_bridge: CrudlBridge):
        """Инициализирует обработчик и ссылку на бизнес-логику CRUDL."""
        self.crudl_bridge = crudl_bridge
        self.next_handler: Optional[BaseCommandHandler] = None

    def set_next(self, handler: "BaseCommandHandler") -> "BaseCommandHandler":
        """Устанавливает следующий обработчик в цепочке."""
        self.next_handler = handler
        return handler

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Передает управление следующему обработчику, если текущий не подходит."""
        if self.next_handler:
            return self.next_handler.handle(request, role)
        return f"Неизвестная команда. Ваша роль: {role}"


class CreateHandler(BaseCommandHandler):
    """Обработчик команды create."""

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Обрабатывает create или делегирует дальше по цепочке."""
        if not request.message.startswith("create "):
            return super().handle(request, role)

        text = request.message.replace("create ", "", 1)
        ok = self.crudl_bridge.create_message(request.username, text)
        return "Сообщение создано" if ok else "Нет прав на Create"


class ReadHandler(BaseCommandHandler):
    """Обработчик команды read."""

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Обрабатывает read или делегирует дальше по цепочке."""
        if request.message != "read":
            return super().handle(request, role)

        messages = self.crudl_bridge.read_messages(request.username)
        return _normalize_response_payload(messages)


class UpdateHandler(BaseCommandHandler):
    """Обработчик команды update."""

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Обрабатывает update или делегирует дальше по цепочке."""
        if not request.message.startswith("update "):
            return super().handle(request, role)

        try:
            parts = request.message.split(" ", 2)
            index = int(parts[1])
            new_text = parts[2]
            ok = self.crudl_bridge.update_message(request.username, index, new_text)
            return "Сообщение обновлено" if ok else "Не удалось обновить сообщение"
        except Exception:
            return "Ошибка формата команды update"


class DeleteHandler(BaseCommandHandler):
    """Обработчик команды delete."""

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Обрабатывает delete или делегирует дальше по цепочке."""
        if not request.message.startswith("delete "):
            return super().handle(request, role)

        try:
            index = int(request.message.split(" ")[1])
            ok = self.crudl_bridge.delete_message(request.username, index)
            return "Сообщение удалено" if ok else "Не удалось удалить сообщение"
        except Exception:
            return "Ошибка формата команды delete"


class ListHandler(BaseCommandHandler):
    """Обработчик команды list."""

    def handle(self, request: CommandRequest, role: Optional[str]) -> str:
        """Обрабатывает list или делегирует дальше по цепочке."""
        if request.message != "list":
            return super().handle(request, role)

        data = self.crudl_bridge.list_data(request.username)
        return _normalize_response_payload(data)


class CommandHandlerFactory:
    """Фабрика обработчиков команд (Factory Method)."""

    @staticmethod
    def create_handler(command_name: str, crudl_bridge: CrudlBridge) -> BaseCommandHandler:
        """Создает конкретный обработчик по имени команды."""
        mapping = {
            "create": CreateHandler,
            "read": ReadHandler,
            "update": UpdateHandler,
            "delete": DeleteHandler,
            "list": ListHandler,
        }
        if command_name not in mapping:
            raise ValueError(f"Неизвестный тип обработчика: {command_name}")
        return mapping[command_name](crudl_bridge)

    @classmethod
    def build_chain(cls, crudl_bridge: CrudlBridge) -> BaseCommandHandler:
        """Собирает полную цепочку обработчиков команд."""
        create_handler = cls.create_handler("create", crudl_bridge)
        read_handler = cls.create_handler("read", crudl_bridge)
        update_handler = cls.create_handler("update", crudl_bridge)
        delete_handler = cls.create_handler("delete", crudl_bridge)
        list_handler = cls.create_handler("list", crudl_bridge)

        create_handler.set_next(read_handler).set_next(update_handler).set_next(delete_handler).set_next(list_handler)
        return create_handler


def handle_message(username, message, db):
    """Обрабатывает сообщение пользователя через цепочку обработчиков."""
    storage = DatabaseStorageImplementor(db)
    crudl_bridge = CrudlBridge(storage)

    storage.ensure_user(username)
    storage.add_log(f"{username} отправил сообщение: {message}")

    roles.check_and_update_role(username, message, storage)
    role = roles.get_user_role(username, storage)

    request = CommandRequest(username=username, message=message)
    chain = CommandHandlerFactory.build_chain(crudl_bridge)
    return chain.handle(request, role)

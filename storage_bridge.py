"""storage_bridge.py
Реализация паттерна Bridge для CRUDL-операций и слоя хранения.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import roles
from constants import CREATE, DELETE, LIST, READ, UPDATE


class StorageImplementor(ABC):
    """Интерфейс реализации хранения данных (Implementor)."""

    @abstractmethod
    def ensure_user(self, username: str) -> None:
        """Создает пользователя при отсутствии записи."""

    @abstractmethod
    def add_log(self, message: str) -> None:
        """Добавляет запись в системный лог."""

    @abstractmethod
    def get_logs(self) -> List[str]:
        """Возвращает системный лог."""

    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict[str, object]]:
        """Возвращает информацию о пользователе."""

    @abstractmethod
    def update_user_role(self, username: str, new_role: str) -> None:
        """Обновляет роль пользователя."""

    @abstractmethod
    def increment_question_count(self, username: str) -> int:
        """Увеличивает счетчик вопросительных сообщений пользователя."""

    @abstractmethod
    def reset_question_count(self, username: str) -> int:
        """Сбрасывает счетчик вопросительных сообщений пользователя."""

    @abstractmethod
    def add_message(self, message: str) -> None:
        """Добавляет новое сообщение в хранилище."""

    @abstractmethod
    def get_all_messages(self) -> List[str]:
        """Возвращает все сообщения."""

    @abstractmethod
    def update_message(self, index: int, new_message: str) -> bool:
        """Обновляет сообщение по индексу."""

    @abstractmethod
    def delete_message(self, index: int) -> bool:
        """Удаляет сообщение по индексу."""


class DatabaseStorageImplementor(StorageImplementor):
    """Реализация хранения через модуль database.py."""

    def __init__(self, db_module):
        """Инициализирует адаптер поверх модуля database.py."""
        self.db = db_module

    def ensure_user(self, username: str) -> None:
        """Создает пользователя при отсутствии записи."""
        self.db.ensure_user(username)

    def add_log(self, message: str) -> None:
        """Добавляет запись в системный лог."""
        self.db.add_log(message)

    def get_logs(self) -> List[str]:
        """Возвращает системный лог."""
        return self.db.get_logs()

    def get_user(self, username: str) -> Optional[Dict[str, object]]:
        """Возвращает информацию о пользователе."""
        return self.db.get_user(username)

    def update_user_role(self, username: str, new_role: str) -> None:
        """Обновляет роль пользователя."""
        self.db.update_user_role(username, new_role)

    def increment_question_count(self, username: str) -> int:
        """Увеличивает счетчик вопросительных сообщений пользователя."""
        return self.db.increment_question_count(username)

    def reset_question_count(self, username: str) -> int:
        """Сбрасывает счетчик вопросительных сообщений пользователя."""
        return self.db.reset_question_count(username)

    def add_message(self, message: str) -> None:
        """Добавляет новое сообщение в хранилище."""
        self.db.add_message(message)

    def get_all_messages(self) -> List[str]:
        """Возвращает все сообщения."""
        return self.db.get_all_messages()

    def update_message(self, index: int, new_message: str) -> bool:
        """Обновляет сообщение по индексу."""
        return self.db.update_message(index, new_message)

    def delete_message(self, index: int) -> bool:
        """Удаляет сообщение по индексу."""
        return self.db.delete_message(index)


class CrudlBridge:
    """Абстракция бизнес-операций CRUDL (Abstraction)."""

    def __init__(self, storage: StorageImplementor):
        """Связывает бизнес-логику с реализацией хранения."""
        self.storage = storage

    def create_message(self, username: str, message: str) -> bool:
        """Создает сообщение с проверкой прав доступа."""
        role = roles.get_user_role(username, self.storage)
        if not roles.has_permission(role, CREATE):
            self.storage.add_log(f"Доступ запрещен: {username} не может создавать сообщения")
            return False
        self.storage.add_message(f"{username}: {message}")
        return True

    def read_messages(self, username: str) -> List[str]:
        """Возвращает сообщения с проверкой прав доступа."""
        role = roles.get_user_role(username, self.storage)
        if not roles.has_permission(role, READ):
            self.storage.add_log(f"Доступ запрещен: {username} не может читать сообщения")
            return []
        return self.storage.get_all_messages()

    def update_message(self, username: str, index: int, new_message: str) -> bool:
        """Обновляет сообщение с проверкой прав доступа."""
        role = roles.get_user_role(username, self.storage)
        if not roles.has_permission(role, UPDATE):
            self.storage.add_log(f"Доступ запрещен: {username} не может изменять сообщения")
            return False
        return self.storage.update_message(index, f"{username}: {new_message}")

    def delete_message(self, username: str, index: int) -> bool:
        """Удаляет сообщение с проверкой прав доступа."""
        role = roles.get_user_role(username, self.storage)
        if not roles.has_permission(role, DELETE):
            self.storage.add_log(f"Доступ запрещен: {username} не может удалять сообщения")
            return False
        return self.storage.delete_message(index)

    def list_data(self, username: str) -> Dict[str, List[str]]:
        """Возвращает данные (messages + logs) с проверкой прав доступа."""
        role = roles.get_user_role(username, self.storage)
        if not roles.has_permission(role, LIST):
            self.storage.add_log(f"Доступ запрещен: {username} не может получать список данных")
            return {}
        return {
            "messages": self.storage.get_all_messages(),
            "logs": self.storage.get_logs(),
        }

"""Тестовая in-memory реализация API database.py."""

from typing import Dict, List, Optional


class DataBaseMock:
    """Минимальная in-memory БД для unit-тестов."""

    def __init__(self):
        self.users: Dict[str, Dict[str, object]] = {
            "admin": {"username": "admin", "role": "Admin", "question_count": 0},
            "user1": {"username": "user1", "role": "User", "question_count": 0},
            "guest": {"username": "guest", "role": "Guest", "question_count": 0},
        }
        self.messages: List[str] = []
        self.logs: List[str] = []

    def ensure_user(self, username: str, default_role: str = "Guest") -> None:
        if username not in self.users:
            self.users[username] = {
                "username": username,
                "role": default_role,
                "question_count": 0,
            }

    def add_log(self, message: str) -> None:
        self.logs.append(message)

    def get_logs(self, limit: int = 200) -> List[str]:
        return self.logs[-limit:]

    def get_user(self, username: str) -> Optional[Dict[str, object]]:
        return self.users.get(username)

    def update_user_role(self, username: str, new_role: str) -> None:
        if username in self.users:
            self.users[username]["role"] = new_role

    def increment_question_count(self, username: str) -> int:
        self.users[username]["question_count"] += 1
        return int(self.users[username]["question_count"])

    def reset_question_count(self, username: str) -> int:
        self.users[username]["question_count"] = 0
        return 0

    def add_message(self, message: str) -> None:
        self.messages.append(message)

    def get_all_messages(self) -> List[str]:
        return list(self.messages)

    def update_message(self, index: int, new_message: str) -> bool:
        if 0 <= index < len(self.messages):
            self.messages[index] = new_message
            return True
        return False

    def delete_message(self, index: int) -> bool:
        if 0 <= index < len(self.messages):
            self.messages.pop(index)
            return True
        return False

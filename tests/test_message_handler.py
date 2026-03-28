"""Unit-тесты цепочки обработчиков message_handler.py."""

import unittest

from message_handler import handle_message
from database_mock import DataBaseMock


class Test_MessageHandler(unittest.TestCase):
    """Проверки обработки CRUDL-команд и неизвестных команд."""

    def setUp(self):
        self.db = DataBaseMock()

    def test_create_allowed_for_admin(self):
        """Админ должен успешно выполнять create."""
        response = handle_message("admin", "create Привет", self.db)
        self.assertEqual(response, "Сообщение создано", "Проверяем, что admin получает успешный ответ create.")
        self.assertIn("admin: Привет", self.db.get_all_messages(), "Проверяем, что сообщение записано в хранилище.")

    def test_create_denied_for_guest(self):
        """Гость не должен иметь права на create."""
        self.db.ensure_user("student", default_role="Guest")
        response = handle_message("student", "create Тест", self.db)
        self.assertEqual(response, "Нет прав на Create", "Проверяем, что Guest получает отказ на create.")
        self.assertEqual(self.db.get_all_messages(), [], "Проверяем, что при отказе данные не записываются.")

    def test_read_and_list_flow(self):
        """read/list должны возвращать данные в ожидаемом формате."""
        handle_message("admin", "create A", self.db)
        read_response = handle_message("admin", "read", self.db)
        list_response = handle_message("admin", "list", self.db)

        self.assertIn("admin: A", read_response, "Проверяем, что read возвращает ранее созданное сообщение.")
        self.assertIn("Messages:", list_response, "Проверяем, что list содержит секцию Messages.")
        self.assertIn("Logs:", list_response, "Проверяем, что list содержит секцию Logs.")

    def test_update_invalid_format(self):
        """Некорректный формат update должен вернуть ошибку формата."""
        response = handle_message("admin", "update x", self.db)
        self.assertEqual(
            response,
            "Ошибка формата команды update",
            "Проверяем, что некорректный update возвращает ошибку формата.",
        )

    def test_delete_invalid_format(self):
        """Некорректный формат delete должен вернуть ошибку формата."""
        response = handle_message("admin", "delete x", self.db)
        self.assertEqual(
            response,
            "Ошибка формата команды delete",
            "Проверяем, что некорректный delete возвращает ошибку формата.",
        )

    def test_unknown_command_contains_role(self):
        """Неизвестная команда должна возвращать сообщение с ролью."""
        response = handle_message("user1", "abc", self.db)
        self.assertIn("Неизвестная команда", response, "Проверяем, что неизвестная команда не теряется в цепочке.")
        self.assertIn("User", response, "Проверяем, что в ответе указывается текущая роль пользователя.")


if __name__ == "__main__":
    unittest.main()

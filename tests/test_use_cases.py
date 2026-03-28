"""Unit-тесты типовых пользовательских сценариев (use cases)."""

import unittest

from message_handler import handle_message
from database_mock import DataBaseMock


class Test_UseCases(unittest.TestCase):
    """Проверки сквозных сценариев: клиентская команда -> CRUDL -> БД."""

    def setUp(self):
        self.db = DataBaseMock()

    def test_admin_full_crudl_cycle(self):
        """Админ должен пройти полный цикл create/read/update/delete/list."""
        r1 = handle_message("admin", "create Первая запись", self.db)
        self.assertEqual(r1, "Сообщение создано", "Проверяем успешное создание сообщения админом.")

        r2 = handle_message("admin", "read", self.db)
        self.assertIn("admin: Первая запись", r2, "Проверяем, что read возвращает созданную запись.")

        r3 = handle_message("admin", "update 0 Обновленная запись", self.db)
        self.assertEqual(r3, "Сообщение обновлено", "Проверяем успешное обновление сообщения.")

        r4 = handle_message("admin", "delete 0", self.db)
        self.assertEqual(r4, "Сообщение удалено", "Проверяем успешное удаление сообщения.")

        r5 = handle_message("admin", "list", self.db)
        self.assertIn("Messages:", r5, "Проверяем, что list возвращает блок сообщений.")
        self.assertIn("Logs:", r5, "Проверяем, что list возвращает блок логов.")

    def test_guest_cannot_create(self):
        """Гость не должен иметь права на create."""
        self.db.ensure_user("guest_case", default_role="Guest")
        response = handle_message("guest_case", "create Нельзя", self.db)

        self.assertEqual(response, "Нет прав на Create", "Проверяем отказ на create для Guest.")
        self.assertEqual(self.db.get_all_messages(), [], "Проверяем, что запись не появилась в БД.")

    def test_user_switches_to_ign_user_after_three_questions(self):
        """После 3 вопросов подряд пользователь должен потерять право create."""
        handle_message("user1", "почему?", self.db)
        handle_message("user1", "зачем?", self.db)
        handle_message("user1", "когда?", self.db)

        response = handle_message("user1", "create Попытка", self.db)
        self.assertEqual(response, "Нет прав на Create", "Проверяем, что после 3 вопросов create запрещен.")
        self.assertEqual(self.db.get_user("user1")["role"], "IgnUser", "Проверяем, что роль стала IgnUser.")

    def test_new_user_is_created_and_can_read_list(self):
        """Новый пользователь должен создаваться автоматически с ролью Guest."""
        response = handle_message("new_user", "list", self.db)

        self.assertIn("Messages:", response, "Проверяем доступ Guest к list после автосоздания пользователя.")
        self.assertEqual(self.db.get_user("new_user")["role"], "Guest", "Проверяем роль Guest для нового пользователя.")

    def test_two_users_write_separate_messages(self):
        """Сообщения должны сохраняться с префиксом имени отправителя."""
        handle_message("admin", "create Сообщение админа", self.db)
        self.db.ensure_user("student", default_role="Admin")
        handle_message("student", "create Сообщение студента", self.db)

        all_messages = self.db.get_all_messages()
        self.assertIn("admin: Сообщение админа", all_messages, "Проверяем наличие сообщения admin.")
        self.assertIn("student: Сообщение студента", all_messages, "Проверяем наличие сообщения student.")


if __name__ == "__main__":
    unittest.main()

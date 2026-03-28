"""Unit-тесты модуля roles.py."""

import unittest

import roles
from constants import CREATE, LIST, READ, ROLE_IGN_USER, ROLE_USER
from database_mock import DataBaseMock


class Test_Roles(unittest.TestCase):
    """Проверки прав доступа и смены ролей."""

    def setUp(self):
        self.db = DataBaseMock()

    def test_permissions_matrix_for_user(self):
        """User должен иметь READ/LIST и не иметь CREATE."""
        self.assertTrue(roles.has_permission(ROLE_USER, READ), "Проверяем, что роль User имеет право READ.")
        self.assertTrue(roles.has_permission(ROLE_USER, LIST), "Проверяем, что роль User имеет право LIST.")
        self.assertFalse(roles.has_permission(ROLE_USER, CREATE), "Проверяем, что роль User не имеет права CREATE.")

    def test_three_questions_switch_to_ign_user(self):
        """После 3 сообщений с '?' роль должна стать IgnUser."""
        for _ in range(3):
            roles.check_and_update_role("user1", "что?", self.db)

        self.assertEqual(
            self.db.get_user("user1")["role"],
            ROLE_IGN_USER,
            "Проверяем, что после трех вопросов подряд роль меняется на IgnUser.",
        )

    def test_non_question_resets_counter(self):
        """Обычное сообщение должно сбрасывать счетчик вопросов."""
        roles.check_and_update_role("user1", "что?", self.db)
        roles.check_and_update_role("user1", "что?", self.db)
        self.assertEqual(
            self.db.get_user("user1")["question_count"],
            2,
            "Проверяем, что счетчик увеличился после двух вопросов.",
        )

        roles.check_and_update_role("user1", "обычное сообщение", self.db)
        self.assertEqual(
            self.db.get_user("user1")["question_count"],
            0,
            "Проверяем, что обычное сообщение сбрасывает question_count.",
        )

    def test_get_user_role_returns_existing_role(self):
        """get_user_role должен вернуть роль существующего пользователя."""
        role = roles.get_user_role("admin", self.db)
        self.assertEqual(role, "Admin", "Проверяем, что get_user_role возвращает корректную роль.")

    def test_get_user_role_for_unknown_user(self):
        """get_user_role должен вернуть None для неизвестного пользователя."""
        role = roles.get_user_role("unknown_user", self.db)
        self.assertIsNone(role, "Проверяем, что для неизвестного пользователя роль равна None.")

    def test_has_permission_for_unknown_role(self):
        """Неизвестная роль не должна иметь прав."""
        allowed = roles.has_permission("NoRole", READ)
        self.assertFalse(allowed, "Проверяем, что неизвестная роль не имеет доступа к операциям.")


if __name__ == "__main__":
    unittest.main()

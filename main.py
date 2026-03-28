# main.py
# Точка входа в приложение
# Взаимодействие с пользователем реализовано через консоль.
# В реальной системе может использоваться Selenium для работы с WhatsApp Web.

import database as db
from message_handler import handle_message

def main():
    """Запускает приложение."""
    print("Система запущена. Введите команды:")
    print("create <текст>, read, update <index> <текст>, delete <index>, list")
    print("exit — для выхода")

    username = "user1"  # текущий пользователь

    while True:
        message = input(">> ")

        if message == "exit":
            print("Выход из системы")
            break

        response = handle_message(username, message, db)

        print("Ответ:", response)

if __name__ == "__main__":
    main()
# main.py
# Точка входа в приложение.

import os
import time

from dotenv import load_dotenv

import database as db
from message_handler import handle_message
from whatsapp_client import WhatsAppClient


load_dotenv()


def _console_mode(username: str):
    print("Система запущена (console mode). Введите команды:")
    print("create <текст>, read, update <index> <текст>, delete <index>, list")
    print("exit — для выхода")

    while True:
        message = input(">> ").strip()

        if message.lower() == "exit":
            print("Выход из системы")
            break

        response = handle_message(username, message, db)
        print("Ответ:", response)


def _whatsapp_mode(username: str):
    chat_name = os.getenv("WA_DEFAULT_CHAT", "").strip()
    if not chat_name:
        raise RuntimeError("Для WhatsApp режима укажите WA_DEFAULT_CHAT в .env")

    poll_interval = int(os.getenv("WA_POLL_INTERVAL_SEC", "3"))
    client = WhatsAppClient()

    last_seen = None
    print(f"Запуск WhatsApp режима. Чат: {chat_name}")

    try:
        client.start()
        client.open()
        print("WhatsApp Web открыт, начинаем цикл чтения/ответа")

        while True:
            incoming = client.read_last_incoming_message(chat_name)
            if incoming and incoming != last_seen:
                print(f"Входящее: {incoming}")
                response = handle_message(username, incoming, db)
                sent = client.send_message(chat_name, str(response))
                print("Ответ отправлен" if sent else "Ошибка отправки ответа")
                last_seen = incoming

            time.sleep(poll_interval)
    except KeyboardInterrupt:
        print("Остановка WhatsApp режима")
    finally:
        client.close()


def main():
    username = os.getenv("APP_USER", "user1")
    app_mode = os.getenv("APP_MODE", "console").strip().lower()

    db.initialize()

    if app_mode == "whatsapp":
        _whatsapp_mode(username)
    else:
        _console_mode(username)


if __name__ == "__main__":
    main()

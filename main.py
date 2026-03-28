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
    allow_outgoing_test = os.getenv("WA_ALLOW_OUTGOING_TEST", "false").strip().lower() in {"1", "true", "yes", "on"}
    debug_logs = os.getenv("WA_DEBUG_LOGS", "false").strip().lower() in {"1", "true", "yes", "on"}
    client = WhatsAppClient()

    last_seen_signature = None
    print(f"Запуск WhatsApp режима. Чат: {chat_name}")
    if allow_outgoing_test:
        print("Включен тестовый режим: чтение исходящих команд.")

    try:
        client.start()
        client.open()
        client.ensure_chat_open(chat_name)
        print("WhatsApp Web открыт, начинаем цикл чтения/ответа")

        while True:
            try:
                event = client.read_last_incoming_event(chat_name, ensure_open=False)
                if not event and allow_outgoing_test:
                    event = client.read_last_outgoing_event(chat_name, ensure_open=False)
            except Exception as error:
                print(f"Ошибка чтения чата: {error}")
                time.sleep(poll_interval)
                continue

            if debug_logs:
                print(f"[DEBUG] Последнее событие: {event}")

            if event:
                incoming = event.get("text", "").strip()
                sender = (event.get("sender") or username).strip() or username
                signature = event.get("signature", incoming)

                if not incoming or signature == last_seen_signature:
                    time.sleep(poll_interval)
                    continue

                normalized = incoming.lower()
                is_command = (
                    normalized.startswith("create ")
                    or normalized.startswith("read")
                    or normalized.startswith("update ")
                    or normalized.startswith("delete ")
                    or normalized.startswith("list")
                )
                if allow_outgoing_test and not is_command:
                    last_seen_signature = signature
                    time.sleep(poll_interval)
                    continue

                print(f"Входящее от {sender}: {incoming}")
                response = handle_message(sender, incoming, db)
                sent = client.send_message(chat_name, str(response))
                if sent:
                    print("Ответ отправлен")
                    warning_text = client.get_last_error()
                    if warning_text:
                        print(f"Примечание отправки: {warning_text}")
                else:
                    error_text = client.get_last_error() or "неизвестная причина"
                    print(f"Ошибка отправки ответа: {error_text}")
                last_seen_signature = signature

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

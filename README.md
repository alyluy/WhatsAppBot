# WhatsAppBot

## Описание выполненных работ

В рамках лабораторной работы реализован рабочий прототип критического сервиса CRUDL с интеграцией WhatsApp Web и PostgreSQL.

Выполнено:
- Перенос хранения данных с моков на реальную PostgreSQL базу.
- Реализован слой подключения к БД в `db_connection.py`.
- Реализован SQL-слой `database.py` с таблицами `users`, `messages`, `logs` и автоинициализацией схемы.
- Поддержан SSH-туннель для подключения к удаленной БД (`ssh_client.py`).
- Реализована ролевая модель (`Admin`, `User`, `Guest`, `IgnUser`) и контроль прав в CRUDL.
- Реализовано правило смены роли: 3 вопросительных сообщения подряд -> `IgnUser`.
- Реализован клиент WhatsApp Web на Selenium (`whatsapp_client.py`) с отправкой и чтением сообщений.
- Реализован основной цикл обработки в `main.py` для режимов `console` и `whatsapp`.
- Добавлен многопользовательский режим для WhatsApp: команды обрабатываются от имени фактического отправителя сообщения.
- Добавлены bootstrap-скрипты для автоматической подготовки окружения и локального запуска.

## Основные модули

- `constants.py` — константы CRUDL и ролей.
- `roles.py` — права доступа и логика смены ролей.
- `crudl.py` — бизнес-операции Create/Read/Update/Delete/List.
- `database.py` — SQL-операции по пользователям, сообщениям и логам.
- `db_connection.py` — подключение к PostgreSQL (локально или через SSH-туннель).
- `ssh_client.py` — управление SSH-туннелем.
- `whatsapp_client.py` — взаимодействие с WhatsApp Web через Selenium.
- `message_handler.py` — обработка команд и маршрутизация операций.
- `main.py` — точка входа и основной цикл сервиса.

## Быстрый запуск

```bash
cd "/Users/LA/Documents/3 курс/ПКС/WhatsAppBot"
./scripts/bootstrap.sh
```

После первого запуска:
- сканируйте QR-код в WhatsApp Web;
- отправляйте команды в чат из `WA_DEFAULT_CHAT`.

Поддерживаемые команды:
- `create <текст>`
- `read`
- `update <index> <новый_текст>`
- `delete <index>`
- `list`

## Полезные команды для БД

Подключение к локальной БД:

```bash
psql -h /tmp -p 5432 -U wbot_user -d whatsapp_bot
```

Назначить пользователя администратором:

```sql
UPDATE users
SET role = 'Admin', question_count = 0
WHERE username = 'Leonid Aleksandrov';
```

Полная очистка стенда:

```sql
TRUNCATE TABLE messages, logs RESTART IDENTITY;
DELETE FROM users WHERE username NOT IN ('admin','user1','guest');
UPDATE users SET role='Admin', question_count=0 WHERE username='admin';
UPDATE users SET role='User', question_count=0 WHERE username='user1';
UPDATE users SET role='Guest', question_count=0 WHERE username='guest';
```

## Частые проблемы

- `session not created` с ChromeDriver:
  версия Chrome и драйвера не совпала; в проекте включен авто-подбор драйвера.
- `TimeoutException` после QR:
  увеличьте `WA_AUTH_TIMEOUT_SEC` в `.env` (например, до `600`).
- `ChromeDriver only supports characters in the BMP`:
  это из-за некоторых emoji; в проекте включена автоматическая фильтрация перед отправкой.

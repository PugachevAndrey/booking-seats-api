# Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Технологический стек](#технологический-стек)
- [Архитектура проекта](#архитектура-проекта)
  - [Структура репозитория](#структура-репозитория)
  - [Доменная модель](#доменная-модель)
  - [Роли и права доступа](#роли-и-права-доступа)
- [API](#api)
  - [Документация](#документация)
  - [Основные маршруты](#основные-маршруты)
- [Перед началом работы](#перед-началом-работы)
  - [Требования](#требования)
  - [Настройка переменных окружения](#настройка-переменных-окружения)
  - [Создание DevContainer](#создание-devcontainer)
  - [И ещё немного подготовки](#и-ещё-немного-подготовки)
- [Запуск проекта](#запуск-проекта)
  - [В режиме отладки](#в-режиме-отладки)
  - [Запустить локально](#запустить-локально)
  - [Запустить в контейнере](#запустить-в-контейнере)
- [Миграции БД](#миграции-бд)
- [Фоновые задачи (Celery)](#фоновые-задачи-celery)
- [Качество кода](#качество-кода)
- [CI/CD](#cicd)
- [Коллекция Postman](#коллекция-postman)
- [Авторы](#авторы)

-----------------------------------

# О проекте

Сервис бронирования столиков в кафе: пользователи выбирают кафе, стол и временной слот, менеджеры управляют кафе, столами и расписанием, а после создания/изменения брони автоматически отправляются уведомления (email, SMS, Telegram).

API построен на **FastAPI** (асинхронный) с **SQLAlchemy 2.0** и **PostgreSQL 17**. Фоновые уведомления вынесены в **Celery + RabbitMQ** и не блокируют HTTP-запросы. Разработка ведётся в **DevContainer** VSCode, продакшен-окружение собирается через **Docker Compose** (приложение, Nginx, PostgreSQL, RabbitMQ, Celery worker, Flower).

В проекте используется Python 3.12 (как наиболее стабильная версия на момент создания шаблона).

В качестве менеджера пакетов используется uv ([Что за зверь?](https://docs.astral.sh/uv/getting-started/installation/))

В качестве стилизатора кода используется [Ruff](https://astral.sh/ruff). Для автоматической проверки стилистики перед коммитами используется [Pre-Commit](https://pre-commit.com).

Все необходимые плагины для VSCode будут установлены в процессе развертывания DevContainer.

# Возможности

- **Аутентификация и авторизация** — JWT-токены (PyJWT), роли `admin` / `manager` / `user`, хэширование паролей Argon2.
- **Управление кафе** — создание (только админ), редактирование (админ или менеджер своего кафе), назначение менеджеров.
- **Столы и временные слоты** — CRUD для столов кафе (`/cafes/{id}/tables`) и временных слотов (`/cafes/{id}/time_slots`).
- **Бронирования** — создание/просмотр/обновление броней с привязкой к столу и временному слоту; контроль прав (клиент видит только свои брони, менеджер — брони своего кафе).
- **Уведомления** — асинхронные задачи Celery: письма клиенту и менеджерам о создании/изменении брони, напоминание за 2 часа до начала (ETA-задача).
- **Медиафайлы** — загрузка изображений (JPG/PNG до 5 Мб) с проверкой содержимого и конвертацией в JPEG через Pillow, раздача файлов по частям.
- **Мониторинг очередей** — Flower для наблюдения за задачами Celery.
- **CI/CD** — проверка стиля Ruff на PR/push и деплой на сервер по push в ветку `develop`.
- **Postman** — готовая коллекция запросов в репозитории.

# Технологический стек

| Область | Технологии |
|---|---|
| Язык | Python 3.12 |
| Веб-фреймворк | FastAPI, Uvicorn |
| ORM | SQLAlchemy 2.0 (asyncio), asyncpg |
| БД | PostgreSQL 17 |
| Миграции | Alembic |
| Валидация | Pydantic v2, pydantic-settings |
| Аутентификация | PyJWT, python-jose, pwdlib (Argon2) |
| Очереди | Celery 5, RabbitMQ |
| Мониторинг задач | Flower |
| Прокси | Nginx |
| Медиа | Pillow, python-multipart |
| Контейнеры | Docker, Docker Compose |
| Пакеты/окружение | uv, pre-commit, Ruff |

# Архитектура проекта

## Структура репозитория

```
├── .devcontainer                   Настройки DevContainer
│   ├── devcontainer.json           Основной настроечный файл
│   ├── devcontainer-lock.json
│   ├── docker-compose.yml          Файл сборки DevContainer и PostgreSQL с помощью Docker Compose
│   ├── Dockerfile                  Файл для билда основного образа DevContainer
│   └── test_tools.sh               Вспомогательный файл
├── .github/workflows               CI/CD
│   ├── deploy.yml                  Деплой на сервер по push в ветку develop
│   └── style_check.yml             Проверка стиля Ruff на PR и push
├── .vscode                         Настройки VSCode
│   └── launch.json                 Настройки для запуска отладки кода
├── celery_app                      Код Celery-воркера
│   ├── Dockerfile                  Образ Celery-воркера
│   ├── celery.py                   Конфигурация Celery (брокер, очереди)
│   └── tasks/notifications.py      Задачи уведомлений (email/SMS/Telegram)
├── infra                           Настройки для формирования Product инфраструктуры
│   ├── docker-compose.yaml         app + nginx + db + rabbitmq + celery_worker + flower
│   ├── .env.example                Файл с настройками
│   └── nginx/nginx.conf            Конфигурация Nginx (прокси, лимит загрузки 5 Мб)
├── media                           Хранилище загруженных изображений (JPEG)
├── postman_collection              Готовая коллекция запросов Postman
├── shared                          Общий код между API и Celery-воркером
│   ├── celery_client.py            Клиент Celery для API (отправка задач, не блокируя запрос)
│   ├── core/                       Настройки, БД, безопасность, enum, ошибки, логирование
│   │   ├── alembic_models.py       Сборка всех моделей для миграций Alembic
│   │   ├── base_model.py           Базовая модель данных с обязательными полями
│   │   ├── db.py                   Настройки для взаимодействия с СУБД
│   │   ├── enums.py                Перечисления: роли пользователей, статусы брони
│   │   ├── security.py             Создание и проверка JWT-токенов
│   │   ├── settings.py             Основные настройки проекта (pydantic-settings)
│   │   └── ...
│   └── models/                     Модели SQLAlchemy (User, Cafe, Table, Slot, Booking, ...)
├── src                             Код FastAPI-приложения
│   ├── api/v1/                     Роутеры: auth, users, cafes, tables, slots, booking, media
│   ├── migrations/                 Миграции Alembic
│   ├── repositories/               Слой доступа к данным
│   ├── schemas/                    Pydantic-схемы запросов и ответов
│   ├── services/                   Бизнес-логика и обработчики ошибок
│   ├── validators/                 Дополнительная валидация
│   ├── alembic.ini                 Настроечный файл Alembic
│   └── main.py                     Главный файл запуска проекта
├── .dockerignore                   Что игнорировать при сборке Docker-образа проекта
├── .gitignore                      Что игнорировать при коммитах
├── .pre-commit-config.yaml         Настройки для проверки стилизации перед коммитом (для pre-commit)
├── .python-version                 Задает версию Python, используемую в проекте (для менеджера UV)
├── Dockerfile                      Файл для сборки Docker-образа API-приложения
├── entrypoint.sh                   Стартовый скрипт: ожидание БД → миграции → uvicorn
├── Makefile                        Вспомогательный файл (lint, format, sync и др.)
├── pyproject.toml                  Основной файл настроек для менеджера UV
├── README.md                       Это сейчас читаем 😎
├── ruff.toml                       Настройки для стилизатора Ruff
└── uv.lock                         Зафиксированные версии пакетов (менеджер UV)
```

Код разделён на слои: **роутеры** (`api/v1`) → **сервисы** (бизнес-логика, `services`) → **репозитории** (доступ к данным, `repositories`) → **модели** (`shared/models`). Общие настройки, безопасность, БД и модели вынесены в пакет `shared`, чтобы API и Celery-воркер работали с одним и тем же кодом.

## Доменная модель

```
User ──‹ CafeManager ›── Cafe ── Table
  │                        │        │        bookings через BookingTablesSlot
  │                        │        └──‹ BookingTablesSlot ›──┐
  │                        └── Slot ──‹ BookingTablesSlot ›───┤
  └──────────────────────────── Booking (user, cafe, guest_number,
                                          note, status, booking_date)
```

- **User** — пользователь: `username`, `email`, `phone`, `tg_id`, пароль (Argon2), роль, `is_active`.
- **Cafe** — кафе: название, адрес, телефон, описание, фото (`media`), менеджеры.
- **CafeManager** — связка пользователь ↔ кафе с признаком активности (`is_active`).
- **Table** — стол кафе: описание и номер места (проверка `seat_number > 0`).
- **Slot** — временной слот кафе: время начала и окончания, описание.
- **Booking** — бронирование: клиент, кафе, количество гостей, примечание, дата, статус.
- **BookingTablesSlot** — состав брони: бронь + стол + временной слот.
- **Media** — метаданные загруженного изображения (файл хранится в `media/`).

Статусы брони: `active`, `booking`, `cancelled`, `completed`.

## Роли и права доступа

| Действие | `user` | `manager` | `admin` |
|---|---|---|---|
| Просмотр кафе, столов, слотов | ✅ | ✅ | ✅ |
| Создание/изменение броней | только свои | все брони своего кафе | любые |
| Управление кафе (создание) | — | — | ✅ |
| Управление кафе, столами, слотами | — | только своего кафе | любые |
| Просмотр списка пользователей | — | только клиенты своего кафе | все |
| Регистрация новых пользователей | — | ✅ | ✅ |
| Загрузка медиафайлов | — | ✅ | ✅ |

# API

## Документация

После запуска приложения интерактивная документация доступна:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health-check: `GET /`

## Основные маршруты

Базовый префикс всех маршрутов — `/api/v1`.

| Метод | Путь | Описание | Доступ |
|---|---|---|---|
| `POST` | `/auth/login` | Вход, получение JWT-токена | все |
| `POST` | `/users` | Регистрация пользователя | аноним, staff |
| `GET` | `/users` | Список пользователей | staff |
| `GET` | `/users/me` | Текущий пользователь | авторизованные |
| `PATCH` | `/users/me` | Обновление своего профиля | авторизованные |
| `GET` | `/users/{user_id}` | Пользователь по ID | staff |
| `PATCH` | `/users/{user_id}` | Обновление пользователя | staff |
| `GET` | `/cafes` | Список кафе | авторизованные |
| `POST` | `/cafes` | Создание кафе | admin |
| `GET` | `/cafes/{cafe_id}` | Кафе по ID | авторизованные |
| `PATCH` | `/cafes/{cafe_id}` | Обновление кафе | staff |
| `GET` | `/cafes/{cafe_id}/tables` | Столы кафе | авторизованные |
| `POST` | `/cafes/{cafe_id}/tables` | Создание стола | staff |
| `GET` | `/cafes/{cafe_id}/tables/{table_id}` | Стол по ID | авторизованные |
| `PATCH` | `/cafes/{cafe_id}/tables/{table_id}` | Обновление стола | staff |
| `GET` | `/cafes/{cafe_id}/time_slots` | Временные слоты кафе | авторизованные |
| `POST` | `/cafes/{cafe_id}/time_slots` | Создание слота | staff |
| `GET` | `/cafes/{cafe_id}/time_slots/{slot_id}` | Слот по ID | авторизованные |
| `PATCH` | `/cafes/{cafe_id}/time_slots/{slot_id}` | Обновление слота | staff |
| `GET` | `/booking` | Список бронирований | авторизованные |
| `POST` | `/booking` | Создание бронирования | авторизованные |
| `GET` | `/booking/{booking_id}` | Бронирование по ID | авторизованные |
| `PATCH` | `/booking/{booking_id}` | Обновление бронирования | авторизованные |
| `POST` | `/media` | Загрузка изображения (JPG/PNG) | staff |
| `GET` | `/media/{media_id}` | Скачивание изображения | все |

Авторизация производится заголовком `Authorization: Bearer <token>`. Токен можно получить через `POST /api/v1/auth/login` (JSON: `username` / `password`).

# Перед началом работы

## Требования

1. Перед началом работы необходимо убедиться, что у вас установлено:
   - Docker ([Скачать](https://www.docker.com/products/docker-desktop/))
   - Плагин Dev Containers для VSCode ([Скачать](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers))

2. В папке `infra` на основе файла `.env.example` создать файл `.env` и заполнить его.

## Настройка переменных окружения

Создайте файл `infra/.env` по образцу `infra/.env.example`. Переменные загружаются через [`shared/core/settings.py`](shared/core/settings.py) автоматически.

### PostgreSQL

| Переменная | Описание |
|---|---|
| `POSTGRES_USER` | Имя пользователя БД |
| `POSTGRES_PASSWORD` | Пароль пользователя БД |
| `POSTGRES_DB` | Название базы данных |
| `POSTGRES_SERVER` | Название или IP сервера БД (в Docker Compose — `db`, в DevContainer — `db`) |
| `POSTGRES_PORT` | Порт БД (по умолчанию 5432) |

### JWT

| Переменная | Описание |
|---|---|
| `SECRET_KEY` | Секретный ключ для подписи токенов |
| `ALGORITHM` | Алгоритм подписи (по умолчанию `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена в минутах (по умолчанию 1440) |

### RabbitMQ (Celery)

| Переменная | Описание |
|---|---|
| `RABBITMQ_USER` | Пользователь RabbitMQ |
| `RABBITMQ_PASSWORD` | Пароль RabbitMQ |
| `RABBITMQ_HOST` | Хост брокера (в Docker Compose — `rabbitmq`) |
| `RABBITMQ_PORT` | Порт брокера (по умолчанию 5672) |

### Уведомления

| Переменная | Описание |
|---|---|
| `SMS_API_KEY` | API-ключ SMS-провайдера (опционально) |
| `SMS_SENDER` | Имя отправителя SMS (опционально) |
| `SMTP_HOST` | SMTP-сервер для отправки email |
| `SMTP_PORT` | Порт SMTP (по умолчанию 587) |
| `SMTP_USER` | Пользователь SMTP |
| `SMTP_PASSWORD` | Пароль SMTP |
| `SMTP_FROM` | Адрес отправителя |
| `SMTP_USE_SSL` | Использовать SSL (`true`/`false`) |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота (опционально) |

3. В файле `.devcontainer/docker-compose.yml` задать нужные значения для следующих параметров:
   - `name` из основного блока
   - `PROJECT_NAME` из блока `remoteEnv`

4. Настройка `docker-compose.yaml`

    В файлах `.devcontainer/docker-compose.yml` и `infra/docker-compose.yaml` в разделе `services` присутствует блок команд и настроек для сборки контейнера с СУБД PostgreSQL.

    По умолчанию этот блок называется `db`. Именно это имя надо указать для параметра `POSTGRES_SERVER` файла `infra/.env`, чтобы при работе в DevContainer можно было подключаться к базе данных.

5. Изменение версии Python

   Хотя изменение версии Python не рекомендуется (ещё не все пакеты переведены на версии >3.12), но никто не мешает экспериментировать.

   Задание версии Python необходимо выполнить в двух местах:
   - файл `.devcontainer/devcontainer.json` параметр `PYTHON_VERSION`
   - файл `Dockerfile` в строке `FROM` после `:` указать ту же версию, что указана в параметре `PYTHON_VERSION`

   **Важно**: Эти версии должны быть одинаковые. *(но никто не мешает разрабатывать в одной, а на прод выкладывать в другой версии)*

## Создание DevContainer

Для запуска создания DevContainer выполнить следующие действия:
- Нажать `Ctrl+Shift+P` для открытия панели команд
- Ввести `Dev Containers: Reopen in Container`
- Выбрать найденный пункт

Начнётся сборка контейнера. Наблюдать за процессом можно в логах.

В процессе создания будут скачаны (при необходимости) нужные образы контейнеров, установлен менеджер пакетов UV, настроено виртуальное окружение проекта, установлены базовые зависимости.

**Обратите внимание:** Линтеры в VSCode не всегда сразу определяют, какие пакеты установлены, и помечают их как не известные. Нужно или подождать немного (или много, тут как повезёт) или перезапустить VSCode не отключаясь от DevContainer (при запуске она сама к нему подключится).

## И ещё немного подготовки

Так как разработка и запуск проекта теперь будет вестись внутри контейнера, то общаться с GitHub-ом сразу не получится. Ведь в контейнере он ещё не настроен, ключи доступа не прописаны.

Что делаем:
1. Настраиваем Git
   - открываем терминал в VSCode
   - выполняем команду `git config --global user.name <Ваше имя>`
   - выполняем команду `git config --global user.email <Ваш email на github-е>`

2. Настраиваем SSH ключи:
   - *вариант 1*: копируем публичный и закрытый ключи (с которыми подключаетесь к GitHub) с хоста в контейнер (в папку `/home/vscode/.ssh`). После этого проверить права доступа к файлам ключей — должно быть `-rw-------` у закрытого ключа и `-rw-r--r--` у открытого ключа. При необходимости поменять права командой `chmod`.
   - *вариант 2*: создаём в контейнере новую пару ключей и прописываем открытый ключ на GitHub в разделе `Settings->SSH and GPG keys` своего профиля.

# Запуск проекта

## В режиме отладки

- Находясь в VSCode, нажать `F5` или перейти на вкладку `Run and Debug` (`Ctrl+Shift+D`) и нажать на зелёную стрелочку.
- Проект запустится на 8000 порту (можно поменять в файле `.vscode/launch.json`) в рамках DevContainer.

## Запустить локально

- Находясь в VSCode, открыть терминал, дождаться активации виртуального окружения.
- Перейти в папку `src` (`cd src`).
- Выполнить команду `python main.py`.
- Проект запустится на 8000 порту (можно поменять в файле [`main.py`](src/main.py:66) в строке `uvicorn.run(app, host='0.0.0.0', port=8000)`).

Если нужны фоновые уведомления, дополнительно запустите Celery-воркер (из корня проекта):

```bash
uv run celery -A celery_app.celery worker -Q notifications,celery --loglevel=info
```

## Запустить в контейнере

- Выйти из DevContainer (ну или установить внутри него Docker Engine 😎). Для этого войти в командную панель (`Ctrl+Shift+P`) и выполнить команду `Dev containers: Reopen Folder Locally` (или открыть папку проекта на хосте).
- Открыть терминал, перейти в папку `infra`.
- Выполнить команду `docker compose up --build`. Для запуска в режиме демона добавить ключ `-d`. Дождаться запуска контейнеров.

Docker Compose поднимет окружение целиком:

| Сервис | Порт (хост) | Описание |
|---|---|---|
| `app` | `8000` | FastAPI-приложение (после старта выполняет миграции Alembic) |
| `nginx` | `80` | Обратный прокси к приложению, лимит загрузки файлов 5 Мб |
| `db` | `5432` | PostgreSQL 17 |
| `rabbitmq` | `5672`, management UI `15672` | Брокер сообщений Celery |
| `celery_worker` | — | Воркер очередей `notifications` и `celery` |
| `flower` | `5555` | Веб-интерфейс мониторинга задач Celery |

После запуска:

- API: `http://localhost:8000` (или `http://localhost` через Nginx)
- Swagger UI: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672`
- Flower: `http://localhost:5555`

# Миграции БД

Миграции выполняются при старте контейнера автоматически (см. [`entrypoint.sh`](entrypoint.sh:9) — `alembic upgrade head`). Для ручного управления из DevContainer:

```bash
# Применить все миграции
cd src && uv run alembic upgrade head

# Сгенерировать новую миграцию по изменению моделей
cd src && uv run alembic revision --autogenerate -m "описание изменения"

# Посмотреть текущую ревизию и историю
cd src && uv run alembic current
cd src && uv run alembic history
```

Все модели подключаются к миграциям через [`shared/core/alembic_models.py`](shared/core/alembic_models.py).

# Фоновые задачи (Celery)

Celery-воркер (сервис `celery_worker`) слушает очередь `notifications` и обрабатывает задачи из [`celery_app/tasks/notifications.py`](celery_app/tasks/notifications.py). API отправляет задачи без блокировки запроса через [`shared/celery_client.py`](shared/celery_client.py).

| Задача | Триггер | Что делает |
|---|---|---|
| `notify_booking_created` | создание брони | Email клиенту и менеджерам кафе |
| `notify_booking_updated` | обновление брони | Email клиенту и менеджерам кафе |
| `notify_booking_reminder` | создание брони (ETA — 2 часа до начала) | Напоминание о предстоящей брони |
| `send_sms` | вручную | Отправка SMS |
| `send_email` | вручную | Отправка email |
| `send_telegram` | вручную | Отправка в Telegram (заглушка) |

Напоминание планируется с отложенным стартом (ETA) через RabbitMQ, поэтому брокер и воркер обязаны быть запущены, иначе задача будет ожидать в очереди.

# Качество кода

Проверка стиля выполняется Ruff и pre-commit. Доступные команды Makefile:

```bash
make lint       # ruff check ./src
make format     # ruff format ./src
make sync       # синхронизация зависимостей + установка pre-commit
make freeze     # заморозка зависимостей в /tmp/requirements.txt
```

Hooks pre-commit запускаются автоматически при коммите. Принудительно проверить весь проект:

```bash
uv run pre-commit run --all-files
```

# CI/CD

GitHub Actions описаны в `.github/workflows`:

- **`style_check.yml`** — проверка стиля Ruff (`ruff check ./src`) при pull request и push в ветки `develop`, `master`, `main`.
- **`deploy.yml`** — деплой на сервер при push в `develop` (или вручную через `workflow_dispatch`): по SSH выполняется `git fetch/reset`, затем `docker compose up -d --build` из папки `infra`.

Для деплоя на сервере должны быть настроены секреты и переменные репозитория: `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY`, `DEPLOY_PATH`, а в `infra/.env` — заполненное окружение.

# Коллекция Postman

В репозитории лежит готовая коллекция запросов — [`postman_collection/booking.postman_collection.json`](postman_collection/booking.postman_collection.json). Импортируйте её в Postman для быстрого знакомства с API.

# Авторы

Проект разработан командой:

- [Lyaisan96](https://github.com/Lyaisan96)
- [Sibnum](https://github.com/Sibnum)
- [PugachevAndrey](https://github.com/PugachevAndrey)
- [pitonyashka](https://github.com/pitonyashka)
- [katarina74](https://github.com/katarina74)

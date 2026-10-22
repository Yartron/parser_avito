# Avito Parser

**Avito Parser** — инструмент для автоматического мониторинга новых объявлений на Avito с мгновенными уведомлениями (Telegram, VK) и экспортом в Excel. Подходит продавцам, аналитикам и всем, кто следит за ценами и предложениями.

![CI](https://github.com/Yartron/parser_avito/actions/workflows/ci.yml/badge.svg)
![Release](https://github.com/Yartron/parser_avito/actions/workflows/release.yml/badge.svg)
![Docker image](https://github.com/Yartron/parser_avito/actions/workflows/docker.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Docker](https://img.shields.io/badge/docker-ghcr.io-2496ED?logo=docker&logoColor=white)

![Avito Parser GUI](docs/media/gui.gif)

> 📜 Полная [история изменений](docs/CHANGELOG.md) · актуальная версия `3.2.23`
> Оригинальный проект: [Duff89/parser_avito](https://github.com/Duff89/parser_avito)

---

## ✨ Возможности

| Категория | Что умеет |
|---|---|
| 📌 Мониторинг | Новые объявления в реальном времени, отслеживание изменения цены, до 100 ссылок (в CLI без ограничений) |
| ⚙️ Фильтры | Чёрный/белый список слов, регион, продавцы, ограничение по времени публикации и цене |
| 📬 Уведомления | Telegram (несколько получателей), VK (несколько получателей), игнорирование просмотренных |
| 💾 Хранение | Экспорт в Excel (одним файлом или по файлу на ссылку), память о просмотренных объявлениях |
| 🛡 Обход блокировок | Прокси с автосменой IP, сторонний сервис cookies (spfa), собственные cookies |
| 🚀 Режимы запуска | GUI (Windows/Linux/macOS), CLI-режим для серверов, Docker 24/7 |

---

## 🚀 Быстрый старт

### Вариант 1: готовый .exe (Windows)

1. Скачай архив со страницы [релизов](https://github.com/Duff89/parser_avito/releases)
2. Запусти `AvitoParser.exe`
3. Заполни настройки (уведомления, ссылки Avito)
4. Нажми **Старт**

### Вариант 2: Python (Windows / Linux / macOS)

Требуется **Python 3.11+**.

```bash
git clone https://github.com/Yartron/parser_avito.git
cd parser_avito

pip install -r requirements.txt
python AvitoParser.py    # режим с графическим интерфейсом
python parser_cls.py     # серверный режим (без GUI)
```

Нужны только `make`-команды? См. [Makefile](Makefile): `make venv`, `make test`, `make lint`.

### Вариант 3: Docker (сервер, 24/7)

```bash
cp .env.example .env     # заполни токены (см. раздел ниже)
touch database.db
docker-compose up -d
```

Подробно про серверы, VPS и compose-файл — в [docs/DOCKER.md](docs/DOCKER.md).

---

## 🔐 Секретные данные и файл .env

Токены и ключи **не обязательно** хранить в `config.toml` — для этого есть файл `.env`, который не коммитится и не попадает в Docker-образ:

```bash
cp .env.example .env     # затем заполни значения
```

| Переменная | Что хранит |
|---|---|
| `TG_TOKEN` | токен Telegram-бота |
| `TG_CHAT_ID` | id получателей через запятую (`123456789,987654321`) |
| `VK_TOKEN` | ключ сообщества VK для рассылки |
| `VK_ID` (= `VK_USER_ID`) | id пользователей VK через запятую |
| `COOKIES_API_KEY` | ключ сервиса обхода блокировок (spfa) |
| `PROXY_STRING` | прокси в формате `login:pass@host:port` |
| `PROXY_CHANGE_URL` | ссылка на смену IP мобильного прокси |
| `PROXY_NOTIFIER` | отдельный прокси для Telegram-рассылки |

**Приоритет источников** (выше — сильнее):

```
переменные окружения (export, docker -e)  →  .env  →  config.toml
```

Пустая или незаданная переменная = берётся значение из `config.toml`. Никогда не отправляй `.env` и незамаскированные токены в issue/PR.

Подробности: [.env.example](.env.example) · [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📬 Уведомления

Пошаговая настройка Telegram и VK (создание бота/сообщества, получение token и id) — в [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md).

---

## 📚 Документация

| Документ | О чём |
|---|---|
| [docs/CHANGELOG.md](docs/CHANGELOG.md) | История изменений |
| [docs/DOCS.md](docs/DOCS.md) | Как устроен код, точки расширения (для разработчиков) |
| [docs/CI.md](docs/CI.md) | CI/CD: проверки, релизы exe и Docker-образов |
| [docs/ANTIBLOCK.md](docs/ANTIBLOCK.md) | Обход блокировок: прокси, cookies, spfa |
| [docs/NOTIFICATIONS.md](docs/NOTIFICATIONS.md) | Настройка Telegram и VK-уведомлений |
| [docs/DOCKER.md](docs/DOCKER.md) | Docker, VPS, фоновый 24/7 режим |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Руководство для соавторов: окружение, процесс, PR |

---

## 🛠 Разработка

```bash
make venv    # окружение + зависимости (+ pytest, ruff)
make test    # pytest — быстрые юнит-тесты
make lint    # ruff check . — линтер (конфиг в ruff.toml)
```

CI на каждый PR автоматически проверяет: линтер → тесты (Python 3.11 и 3.12) → сборку Docker-образа ([docs/CI.md](docs/CI.md)).

Хочешь добавить уведомления, новый экспорт или способ работы с cookies? Точки расширения описаны в [docs/DOCS.md](docs/DOCS.md), процесс для соавторов — в [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 🎥 Обзор и видео

- [Обзор последней версии](https://youtu.be/hh4kYBfjRcA)
- [Запуск локально и на сервере — инструкция для новичков](https://youtu.be/_XQW2ApNwiQ)
- [Плейлист разработки](https://www.youtube.com/playlist?list=PLK9kK8z0fpqxPakGZvxo7y6HtCBTYihUF)

---

## 🛠 Обратная связь

Нашёл баг или есть идея — создай [issue](https://github.com/Yartron/parser_avito/issues) (для багов и предложений есть готовые шаблоны).

При описании ошибки укажи:
- ОС и версию парсера
- Способ запуска (exe / Python / Docker)
- Логи (`logs/app.log`)
- `config.toml` — **только с замаскированными токенами и прокси**

---

### ❤️ Поддержка автора

- [YooMoney](https://yoomoney.ru/to/410014382689862)
- Карта: 2204 1201 0103 5539

---

### 📧 Прямая связь с автором

Пожалуйста, не пиши на почту о багах — для этого есть [issue](https://github.com/Yartron/parser_avito/issues).

📧 Email: sergeichopolovich1989@gmail.com

---

> Программное обеспечение предоставляется «как есть» (as is), без явных или подразумеваемых гарантий.
> Автор не гарантирует стабильную работу, соответствие ожиданиям пользователя или отсутствие ошибок.
> Использование осуществляется на собственный риск пользователя.
> Автор не несёт ответственности за любые последствия.

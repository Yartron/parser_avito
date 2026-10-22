"""Загрузка переменных окружения из .env файла.

Зависимость python-dotenv специально не используется:
парсер .env ниже полностью покрывает минимальный формат
KEY=VALUE и не добавляет проектов в requirements.txt.

Формат файла:
    # комментарий
    VK_TOKEN=abcdef123
    TG_CHAT_ID=123456789,987654321
    PROXY_STRING="login:pass@host:port"
"""

import os
from pathlib import Path

from loguru import logger


def _strip_quotes(value: str) -> str:
    """Убирает одинарные/двойные кавычки вокруг значения."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def parse_env_file(path: str | Path) -> dict[str, str]:
    """Парсит .env файл и возвращает словарь ключ-значение."""
    parsed: dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8-sig")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[len("export "):]
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = _strip_quotes(value.strip())
        if not key:
            continue
        parsed[key] = value
    return parsed


def load_env_file(path: str | Path = ".env") -> dict[str, str]:
    """Загружает .env файл, если он существует.

    Переменные, уже установленные в окружении (export, docker env,
    запуск с --watch env...), имеют приоритет и не перетираются.
    Возвращает только реально загруженный из файла словарь.
    """
    env_path = Path(path)
    if not env_path.is_file():
        return {}

    try:
        parsed = parse_env_file(env_path)
    except OSError as err:
        logger.warning(f"Не удалось прочитать .env файл: {err}")
        return {}

    for key, value in parsed.items():
        os.environ.setdefault(key, value)

    return parsed

import os
import tomllib
from dataclasses import fields
from pathlib import Path
from typing import Callable

import tomli_w

from dto import AvitoConfig
from utils.env_loader import load_env_file


def load_avito_config(path: str = "config.toml") -> AvitoConfig:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    known_fields = {field.name for field in fields(AvitoConfig)}
    config = {
        key: value
        for key, value in data["avito"].items()
        if key in known_fields
    }
    apply_env_overrides(config)
    return AvitoConfig(**config)


def save_avito_config(config: dict):
    with Path("config.toml").open("wb") as f:
        tomli_w.dump(config, f)


def _as_str(value: str) -> str:
    return value.strip()


def _as_id_list(value: str) -> list[str]:
    """Парсит список id: "123, 456", "[123,456]", "123;456" -> ["123", "456"]."""
    value = value.strip().strip("[]")
    items = []
    for part in value.replace(";", ",").split(","):
        part = part.strip()
        if part:
            items.append(part)
    return items


# Чувствительные данные можно хранить в .env / переменных окружения
# вместо config.toml. Группа переменных перекрывает значение из конфига,
# только если она реально установлена (не пустая).
ENV_OVERRIDES: dict[str, list[tuple[str, Callable[[str], object]]]] = {
    "tg_token": [("TG_TOKEN", _as_str)],
    "tg_chat_id": [("TG_CHAT_ID", _as_id_list)],
    "vk_token": [("VK_TOKEN", _as_str)],
    "vk_user_id": [("VK_ID", _as_id_list), ("VK_USER_ID", _as_id_list)],
    "cookies_api_key": [("COOKIES_API_KEY", _as_str)],
    "proxy_string": [("PROXY_STRING", _as_str)],
    "proxy_change_url": [("PROXY_CHANGE_URL", _as_str)],
    "proxy_notifier": [("PROXY_NOTIFIER", _as_str)],
}


def apply_env_overrides(config: dict) -> dict:
    """Применяет значения из .env / окружения поверх значений из config.toml.

    Изменяет словарь на месте и возвращает его. Значение из окружения
    берётся только если переменная установлена и не пустая.
    """
    load_env_file()
    for field_name, sources in ENV_OVERRIDES.items():
        for env_name, caster in sources:
            raw = os.environ.get(env_name)
            if raw is not None and raw.strip() != "":
                config[field_name] = caster(raw)
                break
    return config

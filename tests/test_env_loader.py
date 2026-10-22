import os
import tempfile
from pathlib import Path

from load_config import _as_id_list, apply_env_overrides
from utils.env_loader import parse_env_file
from dto import AvitoConfig


def test_parse_env_file_handles_quotes_comments_and_export():
    with tempfile.TemporaryDirectory() as tmp_dir:
        env_path = Path(tmp_dir) / ".env"
        env_path.write_text(
            "# comment\n"
            "export VK_TOKEN=\"abc123\"\n"
            "TG_TOKEN='token-in-quotes'\n"
            "VK_ID=1234567\n"
            "IGNORED_WITHOUT_EQUALS\n",
            encoding="utf-8",
        )

        parsed = parse_env_file(env_path)

        assert parsed == {
            "VK_TOKEN": "abc123",
            "TG_TOKEN": "token-in-quotes",
            "VK_ID": "1234567",
        }


def test_as_id_list_various_formats():
    assert _as_id_list("123, 456") == ["123", "456"]
    assert _as_id_list("[123,456]") == ["123", "456"]
    assert _as_id_list("123;456") == ["123", "456"]
    assert _as_id_list("") == []


def test_apply_env_overrides_replaces_config_values(monkeypatch):
    config = {
        "tg_token": "from-file",
        "tg_chat_id": ["from-file"],
        "vk_token": "",
        "vk_user_id": [],
    }
    monkeypatch.setenv("TG_TOKEN", "from-env")
    monkeypatch.setenv("VK_ID", "111,222")

    apply_env_overrides(config)

    assert config["tg_token"] == "from-env"
    assert config["tg_chat_id"] == ["from-file"]  # TG_CHAT_ID не задан
    assert config["vk_token"] == ""
    assert config["vk_user_id"] == ["111", "222"]
    # Переменные оверрайдов не должны «просачиваться» в окружение
    assert os.environ.get("VK_TOKEN") != "from-env"


def test_apply_env_overrides_picks_first_non_empty_value(monkeypatch):
    config = {"vk_user_id": []}
    monkeypatch.setenv("VK_USER_ID", "999")
    monkeypatch.setenv("VK_ID", "888")

    apply_env_overrides(config)

    # VK_ID объявлен первым в ENV_OVERRIDES, поэтому имеет приоритет
    assert config["vk_user_id"] == ["888"]


def test_load_avito_config_applies_env(monkeypatch, tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        '[avito]\n'
        'tg_token = "file-token"\n'
        'vk_user_id = []\n'
        'urls = ["https://www.avito.ru/test"]\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("TG_TOKEN", "env-token")

    from load_config import load_avito_config

    monkeypatch.chdir(tmp_path)
    Path(".env").write_text("", encoding="utf-8")

    config = load_avito_config("config.toml")

    assert config.tg_token == "env-token"
    assert config.urls == ["https://www.avito.ru/test"]


def test_build_notifier_is_safe_without_ids(monkeypatch):
    # Токен есть, но список получателей не задан (None) — не должно упасть
    from integrations.notifications.factory import build_notifier

    config = AvitoConfig(urls=[], tg_token="token", tg_chat_id=None, vk_user_id=None)
    notifier = build_notifier(config)
    assert notifier is not None

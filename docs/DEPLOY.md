# Деплой на сервер (Docker 24/7)

Руководство для серверного режима: без GUI, без Windows. Контейнер запускает
`python parser_cls.py` (CLI). Образ публикуется автоматически: тег `vX.Y.Z` →
`docker.yml` → `ghcr.io/yartron/parser_avito:<версия>` (+ `latest`).

---

## 1. Первая установка

### Подготовка сервера

```bash
# Docker + Compose (Ubuntu/Debian)
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker $USER      # перелогинься после этого
docker --version                   # проверка
```

### Каталог проекта

```bash
sudo mkdir -p /opt/avito && cd /opt/avito
sudo chown $USER:$USER /opt/avito

# скопируй docker-compose.yml и .env.example из репозитория
# (scp, wget raw-файла с GitHub — как удобно)
```

`/opt/avito` — дефолтный путь для авто-деплоя; другой путь задай секретом
`DEPLOY_DIR` (см. раздел 3).

### Секреты в .env

```bash
cp .env.example .env
nano .env          # заполни TG_TOKEN/TG_CHAT_ID, VK_TOKEN/VK_ID, прокси
```

Затем в `docker-compose.yml` подключи его (раскомментируй):

```yaml
    env_file:
      - .env
```

### Файлы-маунты и запуск

```bash
touch database.db cookies.json    # пустые bind-файлы для volumes
docker compose pull
docker compose up -d
docker compose logs -f            # убедись, что парсер стартовал
```

Проверка: `docker compose ps` — контейнер `avito` в состоянии `running`,
в логах — строки запуска `AvitoParse vX.Y.Z`.

> 💡 Добавь `./logs:/app/logs` в раздел volumes compose-файла — тогда логи
> переживают обновления контейнера и лежат на хосте.

---

## 2. Обновление версии

### Полный цикл релиза (с твоей машины)

```bash
nano version.py                    # VERSION = "3.2.24"
nano docs/CHANGELOG.md             # блок [3.2.24] - дата
git switch -c feat/3.2.24 && git commit -am "feat: 3.2.24" && git push -u origin feat/3.2.24
# → PR, зелёный CI, merge

git tag v3.2.24 && git push origin v3.2.24
# → образ собран и опубликован (действия: ~15-20 мин, multi-arch)
```

### Если деплой ещё ручной (секреты не настроены)

На сервере:

```bash
cd /opt/avito
docker compose pull
docker compose up -d --remove-orphans
docker image prune -f
# или просто: make update (если скопировал Makefile)
```

### Если настроен авто-деплой

Ничего делать на сервере не нужно: после сборки образа `deploy.yml` сам
подключится по SSH и выкатит ровно ту версию, которую собрал тег.

---

## 3. Настройка автоматического деплоя (deploy.yml)

Workflow деплоя уже в репозитории — нужно один раз выдать ему SSH-доступ.

### Шаг 1. SSH-ключ для деплоя

На сервере:

```bash
# создай отдельный ключ (не свой личный) на своей машине
ssh-keygen -t ed25519 -f ~/.ssh/avito_deploy -C "avito-deploy" -N ""

# добавь публичный ключ на сервер
cat ~/.ssh/avito_deploy.pub | ssh root@SERVER_IP 'cat >> ~/.ssh/authorized_keys'

# проверь, что вход работает без пароля
ssh -i ~/.ssh/avito_deploy root@SERVER_IP 'echo ok'
```

### Шаг 2. Секреты

На своей машине (где авторизован gh):

```bash
gh secret set SSH_HOST --body "IP_СЕРВЕРА"
gh secret set SSH_USER --body "root"                 # или отдельный docker-пользователь
gh secret set SSH_KEY < ~/.ssh/avito_deploy          # приватный ключ, НЕ .pub
# опционально, если путь не /opt/avito:
gh secret set DEPLOY_DIR --body "/srv/avito"
```

На сервере в `/root/.ssh/authorized_keys` должен оказаться публичный ключ.

### Шаг 3. Проверка

```bash
# ручной деплой latest tag (без ожидания релиза)
gh workflow run "Deploy to server" --repo Yartron/parser_avito
gh run list --repo Yartron/parser_avito --limit 3        # статус
```

Дальше всё идёт само: версионный тег → сборка образа → автодеплой.

---

## 4. Операции на сервере

```bash
docker compose logs -f parser_avito    # логи в реальном времени
docker compose restart                 # перезапуск (например, после правки config.toml)
docker compose down                    # остановить
docker compose ps                      # статус
docker image ls | grep parser_avito    # список выкачанных версий
```

Структура данных в `/opt/avito` (переживает обновления — bind-маунты):

| Файл/каталог | Что это |
|---|---|
| `database.db` | Память о просмотренных объявлениях |
| `cookies.json` | Свои cookies (если используешь) |
| `config.toml` | Основные настройки (можно держать бот `read-only`) |
| `result/` | Экспорт Excel |
| `logs/` (если добавить маунт) | Логи loguru |

---

## 5. Если что-то пошло не так

| Симптом | Что проверить |
|---|---|
| Контейнер сразу падает | `docker compose logs --tail=50` — обычно неверный config.toml или нет прокси для spfa |
| `pull` не выкачивает новую версию | Убедись, что `docker.yml` завершился success и образ в [пакетах](https://github.com/Yartron/parser_avito/pkgs/container/parser_avito) опубликован |
| deploy.yml падает с «Не заданы секреты» | Не созданы SSH_HOST/SSH_USER/SSH_KEY — см. раздел 3 |
| При SSH-деплое `docker compose pull` падает | На сервере нет прав GHCR: образ публичный, но если закроешь репо — `docker login ghcr.io` с токеном `read:packages` |
| Уведомления не приходят | Проверь `.env`: `docker compose exec parser_avito env \| grep -E 'TOKEN\|CHAT'` |

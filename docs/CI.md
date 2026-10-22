# CI/CD проекта

Проект использует GitHub Actions. Все workflows лежат в `.github/workflows/`.

Что и когда запускается:

```
                        ┌──────────────────────────────────────────────┐
  PR / push в master ─►│  ci.yml                                      │
                       │   • lint         → ruff check .              │
                       │   • tests        → pytest, Python 3.11/3.12  │
                       │   • docker-build → сборка образа (без push)  │
                       └──────────────────────────────────────────────┘

  тег vX.Y.Z ─────────►  docker.yml: собирает и публикует образ
                         ghcr.io/<owner>/parser_avito:<версия> (+ latest)
                         для linux/amd64 и linux/arm64
                               │
                               ▼  (после success)
                         deploy.yml: SSH на сервер →
                         docker compose pull && docker compose up -d

  понедельник ────────►  dependabot.yml: PR с обновлениями
                         github-actions и pip-зависимостей
```

> Примечание: workflow релиза `.exe` (PyInstaller/Windows) удалён из форка —
> этот режим не поддерживается: GUI/Windows-сборки живут в оригинальном
> [Duff89/parser_avito](https://github.com/Duff89/parser_avito/releases).

---

## ci.yml — Основные проверки

**Триггеры:** `pull_request` в `master` и `push` в `master`.
Смысл: плохое изменение мы узнаём **до** слияния, а не в релизе.

| Job | Что делает | Почему так |
|---|---|---|
| `lint` | `ruff check .` по конфигу [ruff.toml](../ruff.toml) | Версия ruff закреплена (`pip install ruff==0.17.1`), иначе выпуск новой версии ruff меняет набор правил и CI становится красным без причины |
| `tests` | `pytest -v --tb=short` на Python **3.11** и **3.12** (матрица) | README обещает поддержку 3.11+; тесты быстрые (~1 сек) и не требуют сети |
| `docker-build` | `docker/build-push-action` с `load: true` — только сборка, **без пуша** | Сломанный Dockerfile лучше поймать до релиза, а не в момент публикации; кэш слоёв — `type=gha` |

Экономия раннеров: concurrency-группа отменяет устаревшие раны той же ветки (например, при быстрых push подряд).

Секреты: используется только встроенный `GITHUB_TOKEN`, сторонние секреты не нужны. Публикация контейнеров из CI при открытии PR не выполняется — пуш образа только в релизных workflows.

---

## release.yml — Релиз .exe (Windows)

> ❌ **Удалён из форка.** GUI/Windows не поддерживаются, exe-сборки есть
> в оригинальном [Duff89/parser_avito/releases](https://github.com/Duff89/parser_avito/releases).
> История: push в master запускал PyInstaller-сборку, версионированную по `version.py`.

---

## deploy.yml — Автоматический деплой на сервер

**Триггеры:** успешное завершение `docker.yml` (после публикации образа по тегу), а также ручной запуск (`workflow_dispatch`, деплоит `latest`).

Шаги:
1. Проверка секретов: `SSH_HOST`, `SSH_USER`, `SSH_KEY` (не заданы → джоб падает с инструкцией по настройке).
2. Вычисление версии образа из тега сборки (`v3.2.24` → `3.2.24`); неопциональный секрет `DEPLOY_DIR` (по умолчанию `/opt/avito`).
3. SSH (appleboy/ssh-action@v1): `cd $DEPLOY_DIR && docker compose pull && docker compose up -d --remove-orphans && docker image prune -f` + вывод статуса и хвоста логов.
4. Версия образа пробрасывается в compose через `IMAGE_TAG` — выкатывается ровно та версия, которую собрал релизный тег, а не «последний опубликованный latest».

Сетап SSH-ключа и секретов — в [DEPLOY.md](DEPLOY.md), раздел 3.

---

## docker.yml — Релиз Docker-образа

**Триггеры:** тег `v*.*.*` или ручной запуск (`workflow_dispatch`).

Собирает мульти-архитектурный образ (`linux/amd64` + `linux/arm64`) и публикует в GHCR:
- `ghcr.io/<owner>/parser_avito:<версия без v>`
- `ghcr.io/<owner>/parser_avito:latest`

Права: `packages: write`. Для автопубликации ничего настраивать не нужно — GHCR доступен через `GITHUB_TOKEN`.

---

## Полный процесс релиза «с нуля»

### 1. Обновить CHANGELOG и версию

```bash
# docs/CHANGELOG.md — новый блок [x.y.z] - дата (смотри формат прошлых блоков)
# version.py        — VERSION = "x.y.z"
git checkout -b feat/x.y.z
git commit -am "feat: x.y.z release notes и bump версии"
git push -u origin feat/x.y.z
# → открыть PR, дождаться зелёного CI, смержить в master
```

### 2. Собрать Docker-образ и выкатить на сервер

```bash
git pull origin master
git tag vX.Y.Z
git push origin vX.Y.Z
# → docker.yml соберёт и опубликует образ (~15-20 мин)
# → deploy.yml автодеплой (если настроены SSH-секреты, иначе вручную:
#   на сервере: cd /opt/avito && docker compose pull && docker compose up -d)
```

### 3. Проверить результат

- Образ обновился в [пакетах GitHub](https://github.com/Yartron/parser_avito/pkgs/container/parser_avito)
- Быстрая проверка: `docker pull ghcr.io/<owner>/parser_avito:x.y.z`
- Если включен авто-деплой — `gh run list` покажет зелёный `Deploy to server`, на сервере `docker compose ps` — свежая версия

---

## Локальная проверка перед PR

То же самое, что делает CI, доступно локально через Makefile:

```bash
make lint    # ruff check .   — то же, что job lint
make test    # pytest -v      — то же, что job tests
docker build -t parser_avito:local .     # то же, что job docker-build
```

---

## Dependabot

Обновляет две экосистемы по понедельникам: `github-actions` и `pip` (префикс коммитов `deps:`).

- Обновления major-версий actions (`@v4` → `@v5`) — небольшие, смержим после зелёного CI.
- Пакеты `requirements.txt` построчно закреплены (`==`). Major-обновления зависимостей — только **отдельным** PR после обсуждения в issue: они влияют на стабильность парсера (см. правила для PR в [CONTRIBUTING.md](../CONTRIBUTING.md)).
- Dependabot-PR содержат только изменения зависимостей, без правок кода.

---

## Разбор упавшего CI

| Симптом | Что проверить |
|---|---|
| ❌ `lint` | Локально `make lint` — покажет файл, строку и правило |
| ❌ `tests` на одной из версий | Открой ран — видно, какой именно Python упал; типичный случай — разное поведение библиотек в 3.11 vs 3.12 |
| ❌ `docker-build` | Сборка локально на том же коммите: `docker build .`; чаще всего — проблема с зависимостями или системой сборки |
| ⏳ CI «висит» | Concurrency отменил старый ран той же ветки — просто дождись появления нового |

## Критерии «зелёного» перед merge

- `lint` — обязателен всегда
- `tests` — обязательны всегда (обе версии Python)
- `docker-build` — обязателен для любых PR: его поломка = сломанный релиз в будущем

---

## Как добавить новый workflow

Образец — `ci.yml`. Правила, которых придерживаемся:
- минимальные **permissions** для job'а (`contents: read` по умолчанию);
- сторонние actions пинить по major-версии (`@v4`, `@v5`) — мажор фиксирует поведение, обновления поддерживает Dependabot;
- любые секреты — только через `${{ secrets.* }}`, никогда в YAML;
- человекочитаемые имена job'ов (`name: Lint (ruff)`).

Если для нового шага нужен секрет (например, smoke-тест уведомлений) — владелец репозитория создаёт его в **Settings → Secrets and variables → Actions**; коммитить секреты нельзя.

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

  push в master ──────►  release.yml: если версия ещё не релизилась —
                         собирает AvitoParser.exe (PyInstaller) и
                         создаёт GitHub Release v<версия>

  тег vX.Y.Z ─────────►  docker.yml: собирает и публикует образ
                         ghcr.io/<owner>/parser_avito:<версия> (+ latest)
                         для linux/amd64 и linux/arm64

  понедельник ────────►  dependabot.yml: PR с обновлениями
                         github-actions и pip-зависимостей
```

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

**Триггер:** push в `master`.

Порядок работы:
1. Читает версию из `version.py` (`VERSION = "x.y.z"`).
2. Через GitHub API проверяет, существует ли уже Release с тегом `v<версия>`; если да — завершается (идемпотентно: повторный push без бампа версии ничего не собирает).
3. Устанавливает зависимости + PyInstaller.
4. Собирает `AvitoParser.exe` (`--onefile --noconsole`, иконка `assets/logo.ico`, в комплект кладётся `config.toml`).
5. Упаковывает ZIP и создаёт GitHub Release `v<версия>` с файлом.

Ключевое: **релиз управляется версией в файле**. Merge в `master` с новым `version.py` = новый релиз.

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

### 2. Собрать exe

После merge в `master` с бампнутой версией `release.yml` соберёт и опубликует релиз автоматически. Проверь вкладку **Releases** и историю запусков в **Actions**.

### 3. Собрать Docker-образ

```bash
git pull origin master
git tag vX.Y.Z
git push origin vX.Y.Z     # → docker.yml запускается и публикует образ
```

### 4. Проверить результат

- Release появился с файлом `AvitoParser_x.y.z.zip`
- Образ обновился в [пакетах GitHub](https://github.com/Yartron/parser_avito/pkgs/container/parser_avito)
- Быстрая проверка: `docker pull ghcr.io/<owner>/parser_avito:x.y.z`

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

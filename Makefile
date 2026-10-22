ifeq ($(OS),Windows_NT)
	CURDIR := $(shell cd)
	NULL_OUT := NUL
	TRUE := rem
else
	CURDIR := $(shell pwd)
	NULL_OUT := /dev/null
	TRUE := true
endif

IMAGE_NAME = parser_avito:latest
CONTAINER_NAME = parser_avito_container

PYTHON ?= python
VENV := $(CURDIR)/.venv
ifeq ($(OS),Windows_NT)
	PYTHON ?= python
	VENV_BIN := $(VENV)/Scripts
	VENV_ACTIVATE := $(VENV)/Scripts/activate
else
	PYTHON ?= python3
	VENV_BIN := $(VENV)/bin
	VENV_ACTIVATE := $(VENV)/bin/activate
endif

.PHONY: build run restart stop logs shell clean rebuild test lint lintfix venv

# 🏗️ Сборка Docker-образа
build:
	docker build -t $(IMAGE_NAME) .

# ▶️ Запуск контейнера в фоне
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-v $(CURDIR):/app \
		$(IMAGE_NAME)

# 🔄 Перезапуск контейнера (если уже запущен)
restart: stop run

# 🧱 Полная пересборка: stop → build → run
rebuild: stop build run

# 🧹 Остановка и удаление контейнера
stop:
	@docker stop $(CONTAINER_NAME) >$(NULL_OUT) 2>&1 || $(TRUE)
	@docker rm $(CONTAINER_NAME) >$(NULL_OUT) 2>&1 || $(TRUE)
	@echo Container stopped and removed.

# 📜 Просмотр логов контейнера
logs:
	docker logs -f $(CONTAINER_NAME)

# 🐚 Подключение внутрь контейнера
shell:
	docker exec -it $(CONTAINER_NAME) bash

# 🗑 Полная очистка (контейнер + образ)
clean: stop
	@docker rmi $(IMAGE_NAME) >$(NULL_OUT) 2>&1 || $(TRUE)
	@echo Image removed.

# 🐍 Создание виртуального окружения + установка зависимостей
# Если несколько версий Python: make venv PYTHON=python3.12
venv:
	@$(PYTHON) -m venv .venv
	@$(VENV_BIN)/$(PYTHON) -m pip install --upgrade pip
	@$(VENV_BIN)/python -m pip install -r requirements.txt pytest ruff
	@echo Виртуальное окружение готово: source .venv/bin/activate (Linux/macOS) или .venv\\Scripts\\activate (Windows)

# ✅ Запуск тестов (в venv, если он есть)
test:
	@if [ -f "$(VENV_ACTIVATE)" ]; then $(VENV_BIN)/python -m pytest -v; \
	elif command -v $(PYTHON) >/dev/null 2>&1; then $(PYTHON) -m pytest -v; \
	else echo "Python не найден. Создайте окружение: make venv"; exit 1; fi

# 🔍 Проверка кода линтером
lint:
	@if [ -f "$(VENV_ACTIVATE)" ]; then $(VENV_BIN)/python -m ruff check .; \
	elif command -v ruff >/dev/null 2>&1; then ruff check .; \
	else echo "Ruff не найден. Установите: make venv"; exit 1; fi

# 📊 Автоисправление замечаний линтера
lintfix:
	@if [ -f "$(VENV_ACTIVATE)" ]; then $(VENV_BIN)/python -m ruff check . --fix; \
	elif command -v ruff >/dev/null 2>&1; then ruff check . --fix; \
	else echo "Ruff не найден. Установите: make venv"; exit 1; fi

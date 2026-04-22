COMPOSE ?= docker compose
MANAGE ?= $(COMPOSE) run --rm web python manage.py
APP ?=
TARGET ?=
ARGS ?=

.PHONY: build run down makemigrations migrate revert showmigrations

build:
	$(COMPOSE) up -d --build

run:
	$(COMPOSE) up -d

stop:
	$(COMPOSE) down

mm:
	$(MANAGE) makemigrations $(APP)

m:
	$(MANAGE) migrate $(ARGS)

revert:
	@if [ -z "$(APP)" ] || [ -z "$(TARGET)" ]; then \
		echo "Usage: make revert APP=finance TARGET=0003"; \
		exit 1; \
	fi
	$(MANAGE) migrate $(APP) $(TARGET)

showmigrations:
	$(MANAGE) showmigrations $(APP)

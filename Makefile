# ==========================================
# VoxPop - Makefile
# ==========================================

.PHONY: help dev dev-build down logs shell migrate makemigrations build push deploy test clean

# Cores
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

# Ajuda
help: ## Mostra esta ajuda
	@echo ''
	@echo 'Uso:'
	@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==========================================
# Desenvolvimento
# ==========================================

dev: ## Sobe toda a stack de desenvolvimento
	docker compose up -d
	@echo ""
	@echo "${GREEN}Stack iniciada!${RESET}"
	@echo ""
	@echo "Servicos disponiveis:"
	@echo "  - Backend:  http://localhost:8000"
	@echo "  - Frontend: http://localhost:5173"
	@echo "  - Mailhog:  http://localhost:8025"
	@echo ""
	docker compose logs -f

dev-build: ## Rebuilda e sobe a stack
	docker compose up -d --build
	docker compose logs -f

down: ## Para todos os containers
	docker compose down

logs: ## Mostra logs (use: make logs service=backend)
	docker compose logs -f $(service)

shell: ## Abre shell Django
	docker compose exec backend python manage.py shell_plus

bash: ## Abre bash no backend
	docker compose exec backend bash

# ==========================================
# Banco de Dados
# ==========================================

migrate: ## Executa todas as migracoes (shared + tenants)
	docker compose exec backend python manage.py migrate_schemas --shared
	docker compose exec backend python manage.py migrate_schemas

migrate-shared: ## Executa apenas migracoes do schema publico
	docker compose exec backend python manage.py migrate_schemas --shared

migrate-tenants: ## Executa apenas migracoes dos tenants
	docker compose exec backend python manage.py migrate_schemas

makemigrations: ## Cria migracoes
	docker compose exec backend python manage.py makemigrations

createsuperuser: ## Cria superusuario
	docker compose exec backend python manage.py createsuperuser

dbshell: ## Abre shell do PostgreSQL
	docker compose exec db psql -U voxpop -d voxpop_db

# ==========================================
# Build e Deploy
# ==========================================

build: ## Build da imagem Docker
	./build.sh

push: ## Build e push para registry
	./build.sh --push

deploy: ## Deploy no Docker Swarm
	@echo "Criando volumes externos (se nao existirem)..."
	docker volume create voxpop_postgres || true
	docker volume create voxpop_redis || true
	docker volume create voxpop_static || true
	docker volume create voxpop_media || true
	@echo ""
	@echo "Fazendo deploy da stack..."
	docker stack deploy -c docker-stack.yml voxpop
	@echo ""
	@echo "${GREEN}Deploy iniciado!${RESET}"
	@echo "Acompanhe com: docker service ls"

undeploy: ## Remove stack do Swarm
	docker stack rm voxpop

# ==========================================
# Testes
# ==========================================

test: ## Executa testes
	docker compose exec backend pytest

test-cov: ## Executa testes com coverage
	docker compose exec backend pytest --cov=apps --cov-report=html

lint: ## Executa linters
	docker compose exec backend ruff check .
	docker compose exec backend black --check .

format: ## Formata codigo
	docker compose exec backend black .
	docker compose exec backend ruff check --fix .

# ==========================================
# Utilitarios
# ==========================================

clean: ## Remove containers, volumes e imagens
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "${GREEN}Limpeza concluida!${RESET}"

ps: ## Lista containers
	docker compose ps

restart: ## Reinicia um servico (use: make restart service=backend)
	docker compose restart $(service)

# ==========================================
# Producao
# ==========================================

prod-logs: ## Logs da stack em producao
	docker service logs -f voxpop_voxpop_app

prod-scale: ## Escala app (use: make prod-scale replicas=3)
	docker service scale voxpop_voxpop_app=$(replicas)

prod-update: ## Atualiza imagem em producao
	docker service update --image ${DOCKER_REGISTRY:-lpcoutinho}/voxpop:${VERSION:-latest} voxpop_voxpop_app

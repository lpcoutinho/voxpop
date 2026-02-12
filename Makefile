# ==========================================
# VoxPop - Makefile
# ==========================================

.PHONY: help dev dev-build down logs shell migrate makemigrations build push deploy test clean frontend frontend-install

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
	@bash dev.sh

dev-build: ## Rebuilda e sobe a stack
	cd backend && docker compose up -d --build
	cd backend && docker compose logs -f

down: ## Para todos os containers
	cd backend && docker compose down

logs: ## Mostra logs (use: make logs service=web)
	cd backend && docker compose logs -f $(service)

shell: ## Abre shell Django
	cd backend && docker compose exec web python manage.py shell_plus

bash: ## Abre bash no backend
	cd backend && docker compose exec web bash

# ==========================================
# Frontend
# ==========================================

frontend: ## Inicia o frontend em modo desenvolvimento
	cd frontend && npm run dev

frontend-install: ## Instala dependencias do frontend
	cd frontend && npm install

# ==========================================
# Banco de Dados
# ==========================================

migrate: ## Executa todas as migracoes (shared + tenants)
	cd backend && docker compose exec web python manage.py migrate_schemas --shared
	cd backend && docker compose exec web python manage.py migrate_schemas

migrate-shared: ## Executa apenas migracoes do schema publico
	cd backend && docker compose exec web python manage.py migrate_schemas --shared

migrate-tenants: ## Executa apenas migracoes dos tenants
	cd backend && docker compose exec web python manage.py migrate_schemas

makemigrations: ## Cria migracoes
	cd backend && docker compose exec web python manage.py makemigrations

createsuperuser: ## Cria superusuario
	cd backend && docker compose exec web python manage.py createsuperuser

dbshell: ## Abre shell do PostgreSQL (apenas para banco local)
	cd backend && docker compose -f docker-compose.local.yml exec db psql -U voxpop -d voxpop_db

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
	cd backend && docker compose exec web pytest

test-cov: ## Executa testes com coverage
	cd backend && docker compose exec web pytest --cov=apps --cov-report=html

lint: ## Executa linters
	cd backend && docker compose exec web ruff check .
	cd backend && docker compose exec web black --check .

format: ## Formata codigo
	cd backend && docker compose exec web black .
	cd backend && docker compose exec web ruff check --fix .

# ==========================================
# Utilitarios
# ==========================================

clean: ## Remove containers, volumes e imagens
	cd backend && docker compose down -v --remove-orphans
	docker system prune -f
	@echo "${GREEN}Limpeza concluida!${RESET}"

ps: ## Lista containers
	cd backend && docker compose ps

restart: ## Reinicia um servico (use: make restart service=web)
	cd backend && docker compose restart $(service)

# ==========================================
# Producao
# ==========================================

prod-logs: ## Logs da stack em producao
	docker service logs -f voxpop_voxpop_app

prod-scale: ## Escala app (use: make prod-scale replicas=3)
	docker service scale voxpop_voxpop_app=$(replicas)

prod-update: ## Atualiza imagem em producao
	docker service update --image ${DOCKER_REGISTRY:-lpcoutinho}/voxpop:${VERSION:-latest} voxpop_voxpop_app

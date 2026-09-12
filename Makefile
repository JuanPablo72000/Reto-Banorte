.PHONY: up down reset seed logs api mcp frontend

up:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build

seed:
	docker compose run --rm seed

logs:
	docker compose logs -f

api:
	docker compose up api

mcp:
	docker compose up mcp

frontend:
	docker compose up frontend
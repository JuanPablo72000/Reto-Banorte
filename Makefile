.PHONY: up down reset seed logs api mcp frontend demo demo-abajo demo-logs demo-reset

up:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build

seed:
	@echo "El seed es automatico: la API aplica migraciones e inserta datos demo al arrancar."

logs:
	docker compose logs -f

api:
	docker compose up api

mcp:
	docker compose up mcp

frontend:
	docker compose up frontend

# Demo completa: levanta todo en segundo plano, espera a que responda y
# muestra el link listo para entrar. Ver scripts/demo.ps1 (lo mismo en
# PowerShell para Windows sin make).
demo:
	docker compose up --build -d
	@powershell -NoProfile -ExecutionPolicy Bypass -File scripts/demo.ps1 -SoloEsperar
	@echo ""
	@echo "Listo para entrar -> http://localhost:3000 (chat)"
	@echo "API: http://localhost:8000/health | MCP: http://localhost:8080"

demo-abajo:
	docker compose down

demo-logs:
	docker compose logs -f

demo-reset:
	docker compose down -v
	docker compose up --build -d

up:
	docker compose up --build

down:
	docker compose down

reset:
	docker compose down -v
	docker compose up --build

seed:
	@echo "El seed es automatico: la API aplica migraciones e inserta datos demo al arrancar."

logs:
	docker compose logs -f

api:
	docker compose up api

mcp:
	docker compose up mcp

frontend:
	docker compose up frontend
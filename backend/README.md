# Backend — BancaAdaptativa.Api

API de datos en **.NET 10 Minimal API + SQLite + JWT**. Expone todo lo que consumen el frontend (directo) y el MCP (vía tools): cuentas, movimientos, transferencias, presupuestos, metas, tarjetas, estados de cuenta, conciliación, preferencias y memoria.

## Estructura

```
src/BancaAdaptativa.Api/
├── Endpoints/      # Auth, Accounts, Transfers, Budgets, SavingsGoals, CreditCards, Users, System
├── Services/       # AuthService, TransferService, BudgetService, SavingsGoalService,
│                   #   CreditCardService, StatementService + StatementGenerationService (trigger nocturno),
│                   #   AccountQueryService, PreferenceService, BusinessClock
├── Models/         # Entidades EF Core (ver docs/datos/)
├── Dtos/           # Records de request/response (camelCase en JSON)
└── Data/           # AppDbContext (UTC, DateOnly, índices únicos) + DbSeeder + Migrations
```

## Endpoints principales (todos con `Bearer {token}` salvo `/auth/*` y sistema)

| Grupo | Ejemplos |
|---|---|
| Auth | `POST /auth/login` (`demo@banorte.mx` / `Demo123!`), `POST /auth/register` |
| Cuentas | `GET /accounts`, `GET /me/account-summary`, `GET /accounts/{id}`, `GET /accounts/{id}/transactions`, `GET /me/transactions`, `GET /accounts/{id}/daily-balances` |
| Transferencias | `POST /transfers/` (crea `pending`), `POST /transfers/{id}/confirm`, `GET /transfers` |
| Finanzas | `GET/POST /me/budgets(/monthly)`, `GET/POST /me/savings-goals` (+ `contribute`, `status`), `GET/POST /me/credit-cards` (+ `pay`, `statements/generate`), `GET /reconciliation` |
| Estados de cuenta | `GET /accounts/{id}/statements`, `.../{statementId}`, `POST .../generate` (idempotente por periodo) |
| Usuario | `GET /users/me`, `GET/PUT /me/preferences` |
| Sistema | `GET /health`, `GET /server-time`, Swagger en `/swagger` |

## Seed demo (determinista)

Al arrancar: `Migrate()` + `DbSeeder.Seed()`. Generador con semilla fija, relativo a hoy: **4 cuentas** (Nómina id 1, Ahorro, Compras en línea, Cuenta antigua bloqueada), **~300 movimientos** de 90 días con vocabulario estable (`nomina`, `super`, `transporte`…), **90 balances diarios** coherentes (saldo = último cierre), **10 transferencias** (6 confirmed, 3 pending confirmables, 1 rejected) con conciliación matched/pending/unmatched, **3 tarjetas** con statement previo, **5 metas** (4 activas), **6 presupuestos** del mes (restaurantes rebasado a propósito), 3 estados de cuenta cerrados, sesiones y eventos de memoria.

**Simulaciones que siempre funcionan**: crear + confirmar transferencia, pagar tarjeta, aportar a meta activa, generar estado de cuenta de un mes previo.

**Regenerar datos**: el seed solo corre con BD vacía. Local: borra `backend/data/app.db` (corre el backend con CWD en `src/BancaAdaptativa.Api`). Docker: `docker compose down -v`.

## Auth

JWT (`Issuer`/`Audience` en `appsettings.json`, expira 60 min). Firma con `Jwt:Key` o env **`JWT_KEY`** (mín. 32 caracteres; el login falla sin ella). CORS permite `localhost:3000/4173/5173`.

## Comandos (requiere .NET SDK 10)

```bash
dotnet build backend/BancaAdaptativa.slnx
dotnet test backend/BancaAdaptativa.slnx        # 103 pruebas (unit + integración)
dotnet run --project backend/src/BancaAdaptativa.Api  # http://localhost:5178
```

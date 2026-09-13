# Puente MCP → Frontend (opción A implementada)

> Dueños: MCP Guillermo · Frontend Juan Pablo · Integración Cain.
> El MCP ejecuta las tools contra `BancaAdaptativa.Api` y devuelve datos
> ya resueltos; el front solo renderiza. Contrato de ejemplo real: bloque
> [4] de `mcp/tests/test_repl_e2e.py`.

## 1. Flujo (opción A)

```
[ChatWindow] --{mensaje, contexto{id_user,id_account,token?}}--> POST /api/chat
  --> lib/mcp/client.ts --subproceso stdio--> python -m app.server.mcp_server
  --> planificar_accion + ejecución de steps (API real / mock)
  <-- ActionPlan ejecutado (JSON [4]) --> PlanRenderer --> tarjeta variable
```

- `frontend/src/app/api/chat/route.ts`: valida el body, llama
  `lib/mcp/client.ts`, devuelve el JSON o `ErrorState` (timeout 120 s).
- `frontend/src/lib/mcp/client.ts`: abstrae el transporte. Hoy `spawn`
  del script (`MCP_SERVER_SCRIPT`, default `../../mcp/app/server/
  mcp_server.py` en dev y `/srv/app/mcp-server/...` en docker);
  propaga `GROQ_API_KEY`, `GEMINI_API_KEY`, `BANORTE_*` y
  `BANORTE_API_TOKEN` al subproceso.
- `frontend/src/lib/types/action-plan.ts`: tipos TS espejo 1:1 de
  `mcp/app/schemas/schemas.py` (`ActionPlan`, `ExecutedStep`,
  `SuggestedAction`, enums `UIHint/IconType/Variant/Tone` — mismo
  vocabulario que `components/ui`: `primary/secondary/ghost/danger`).
- `frontend/src/components/chat/PlanRenderer.tsx`: mapea
  `(ui_hint, tool)` → componente con props (`result` + `visual` +
  `messages[template]`); `suggested_actions` → botones que reinyectan
  el siguiente turno; `needs_confirmation` → `Modal` antes de ejecutar
  transfers; `A11yProvider` gobernado por `accessibility_template` +
  `visual_theme` (CSS vars).

## 2. Mapa tool → componente

| tool | ui_hint | componente |
|---|---|---|
| get_user_context | none | texto + `AccessibilityPanel` |
| get_accounts | summary/table | `AccountsList` |
| get_account_summary | summary | `AccountSummaryCard` (nuevo) |
| get_account_detail | summary | `AccountDetail` |
| get_transactions / get_all_transactions | table | `TransactionsView` |
| get_daily_balance | summary | `BalanceCard`/`BalanceGrid` |
| search_memory_context | none | texto |
| prepare_transfer | form | `TransferFlow` |
| confirm_transfer | confirmation | `Modal` de confirmación |
| get_transfers | table | `TransactionsView` (modo transfers) |
| get_transfer_detail | summary | `TransferDetail` (nuevo) |
| get_reconciliation_status | table | `ReconciliationView` |
| get_statements | table | `StatementsTable` (nuevo) |
| get_statement_detail | summary | `StatementDetail` (nuevo) |
| get_expense_categories | table | `ExpenseCategoriesList` (nuevo) |
| get_budgets_monthly | summary | `BudgetsSummary` (nuevo) |
| get_savings_goals | table | `SavingsGoalsList` (nuevo) |
| get_credit_cards | table | `CreditCardsTable` (nuevo) |
| get_credit_card_statements | table | `StatementsTable` (modo tarjeta) |

## 3. Auth

El front hace login (`POST /auth/login`), guarda el JWT y lo manda en
cada turno (`{token}` en el body de `/api/chat`). El puente lo pasa al
subproceso como `BANORTE_API_TOKEN`; `connection.py` lo prefiere sobre
el auto-login demo. Sin token: demo (`demo@banorte.mx`).

## 4. Opción B (futura): dataRefs, el front fetchea

> NO implementada. Disparadores: privacidad (que saldos no crucen el
> JSON de IA), latencia del subproceso, o múltiples frontends.

- La IA devuelve el plan con `dataRef` (`contracts/a2ui/
  a2ui-mcp-contract.yaml`: `accounts.list`, `getMeAccountSummary`,
  …) en vez de `result`; el front resuelve cada ref con `operationId`
  + `selector` contra `apiBaseUrl` (`lib/api/*`), con `loading/error/
  fallback` por tarjeta (reglas del contrato).
- Requiere: completar `contracts/openapi/` (hoy vacío), implementador
  de dataRefs en `lib/api`, y `suggested_actions` con dataRefs.
- Migración compatible: `PlanRenderer` acepta steps con `result` (A)
  o con `dataRef` (B); el transporte HTTP del MCP
  (`MCP_TRANSPORT=http`, puerto 8080, ver `mcp/Dockerfile`) sirve para
  ambas: sesiones persistentes, sin arrancar intérprete por turno.

## 5. Docker

- `mcp/Dockerfile`: `MCP_TRANSPORT=stdio` por default; con
  `MCP_TRANSPORT=http` levanta streamable-http en `MCP_PORT` (8080).
- `frontend/Dockerfile`: Node 22 + Python 3.12 + `mcp/` copiado a
  `/srv/app/mcp-server` para el subproceso stdio; `MCP_SERVER_SCRIPT`
  apunta ahí. Las keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `JWT_KEY`,
  `BANORTE_API_TOKEN`) se inyectan por `environment:` en compose
  (nunca commiteadas).

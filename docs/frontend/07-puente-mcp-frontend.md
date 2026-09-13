# Puente MCP → Frontend

> Dueños: MCP · Frontend · Integración.
> El MCP ejecuta las tools contra `BancaAdaptativa.Api` y devuelve datos ya resueltos **más gráficas**; el front solo renderiza.

## 1. Flujo

```
[ChatWindow/useChatPlan] --{mensaje, contexto{id_user,id_account,token?}}--> POST /api/chat
  --> lib/mcp/client.ts --subproceso stdio--> mcp/run_turn.py
  --> orquestador.ejecutar_turno: plan IA + steps (API real / mock) + visualizaciones
  <-- ActionPlanUI --> PlanRenderer (steps + gráficas + sugerencias + modal)
```

- `frontend/src/app/api/chat/route.ts`: valida el body (`mensaje` requerido), llama `ejecutarTurno`, devuelve el JSON o `ErrorState` (timeout 120 s).
- `frontend/src/lib/mcp/client.ts`: abstrae el transporte. `ejecutarTurno` hace `spawn` de `run_turn.py` (`MCP_DIR`: `./mcp-server` en docker, `../mcp` en dev); `ejecutarAccion` invoca acciones sin IA (`reset_memoria`). El `token` del contexto viaja como `BANORTE_API_TOKEN`.
- `frontend/src/app/api/memory/reset/route.ts`: `POST {id_user}` → `ejecutarAccion("reset_memoria")` → `{ok:true}` (usado por el panel de accesibilidad).
- `frontend/src/lib/types/action-plan.ts`: tipos TS espejo de `mcp/app/schemas/schemas.py` (`ActionPlanUI`, `ExecutedStep`, `SuggestedAction`, `Visualization`, enums `UIHint/IconType/Variant/Tone` — mismo vocabulario que `components/ui`).
- `frontend/src/components/chat/PlanRenderer.tsx`: mapea `tool` → componente (`REGISTRO`) con props `step` (`result` + `visual` + `messages[plantilla]`); `suggested_actions` → botones con `accion_directa` (tool/arguments exactos que el orquestador fuerza aunque la IA los omita); `needs_confirmation`/`pendiente_confirmacion` → `Modal`; `visualizations` → cuadrícula de gráficas + `BankCard`.
- `useChatPlan` (`lib/hooks/useChatPlan.ts`): estado del turno (plan, cargando, error, hilo) reutilizado por el home y los bloques `CainQuery` de las páginas.

## 2. Mapa tool → componente

| tool | componente | notas |
|---|---|---|
| get_user_context | `UserContextCard` | contexto + perfil |
| get_accounts / get_account_detail | `AccountsPlanList` | lista de cuentas |
| get_account_summary | `AccountSummaryCard` | saldo total |
| get_transactions / get_all_transactions | `TimelineList` | movimientos por día |
| get_daily_balance | `BalancePlanCard` | serie de saldos |
| search_memory_context / prepare_transfer / confirm_transfer | `GenericStepCard` | el flujo de transferencias lo completa el `Modal` de `PlanRenderer` |
| get_transfers | `TransfersTable` | historial |
| get_transfer_detail | `TransferDetail` | detalle |
| get_reconciliation_status | `ReconciliationPlanTable` | conciliación |
| get_statements / get_credit_card_statements | `StatementsTable` | estados de cuenta |
| get_statement_detail | `StatementDetail` | detalle + desglose |
| get_expense_categories | `ExpenseCategoriesList` | dona + lista con barras (vista tarjetas) o tabla (`data-vista="tabla"`) |
| get_budgets_monthly | `BudgetsSummary` | presupuestos |
| get_savings_goals | `SavingsGoalsList` | metas con progreso |
| get_credit_cards | `CreditCardsTable` | tarjetas |

## 3. Visualizaciones (gráficas)

El orquestador devuelve `visualizations` (las de la IA primero + **deterministas** de `mcp/app/ia/visualizaciones.py`, deduplicadas por título, máx. 4). Tipos: `bar` (multi-serie), `line`, `area`, `pie`/`donut`, `bank_card`. Reglas: series de tiempo ascendentes por fecha (con el rango consultado en el título), categorías descendentes por monto, `accessibility_label` completo. El front las ordena en cuadrícula (`donut`/`bank_card` a ancho completo).

## 4. Auth

El front hace login (`POST /auth/login`), guarda el JWT en la sesión y lo manda en cada turno (`token` en el body de `/api/chat`). El puente lo pasa al subproceso como `BANORTE_API_TOKEN`; `connection.py` lo prefiere sobre el auto-login demo. Sin token o sin backend: demo local (`id_user=1`, mocks congruentes con el seed).

## 5. Opción B (futura): dataRefs, el front fetchea

> NO implementada. Disparadores: privacidad (que saldos no crucen el JSON de IA), latencia del subproceso, o múltiples frontends.

- La IA devuelve el plan con `dataRef` (`contracts/a2ui/a2ui-mcp-contract.yaml`) en vez de `result`; el front resuelve cada ref contra `apiBaseUrl` (`lib/api/*`), con `loading/error/fallback` por tarjeta.
- Requiere: completar `contracts/openapi/`, implementador de dataRefs en `lib/api`, y `suggested_actions` con dataRefs.

## 6. Docker

- `mcp/Dockerfile`: stdio por default; con `MCP_TRANSPORT=http` levanta streamable-http en `MCP_PORT` (8080).
- `frontend/Dockerfile`: Node 22 + Python 3.12 + `mcp/` copiado a `/srv/app/mcp-server` para el subproceso stdio. Las keys (`GROQ_API_KEY`, `GEMINI_API_KEY`, `JWT_KEY`) se inyectan por `environment:` en compose (nunca commiteadas).

# Matriz de filtros para consultas e IA

Este anexo consolida todos los filtros disponibles en la API y expuestos al contrato A2UI/MCP (`contracts/a2ui/a2ui-mcp-contract.yaml`). Permite a la IA emitir `dataRefs` acotados por fechas, categorías, cuentas, estados y texto, habilitando interfaces dinámicas y personalizadas sin exponer datos sensibles.

## 1. Matriz general de filtros

| dataRef | Endpoint | Filtros disponibles (Query Params) | Ejemplo de uso IA |
|---|---|---|---|
| `accounts.list` | `GET /accounts` | `status` (`active`, `blocked`), `accountType` (`debito`, `credito`) | "Muestra solo las cuentas de débito activas" |
| `transactions.list` | `GET /accounts/{id}/transactions` | `from` (date), `to` (date), `category` (texto libre), `expenseCategory` (código de catálogo), `direction` (`credit`/`debit`), `status` (`posted`/`pending`), `search` (texto libre), `limit` (1-100) | "Movimientos del último mes en supermercados" |
| `transactions.global` 🆕 | `GET /me/transactions` | `accountId` (opcional), `from`, `to`, `category`, `expenseCategory`, `direction`, `status`, `search`, `limit` | "Búsqueda transversal de gastos en todas mis cuentas" |
| `dailyBalances.list` | `GET /accounts/{id}/daily-balances` | `from` (date), `to` (date) | "Gráfica de saldo de los últimos 15 días" |
| `transfers.list` 🆕 | `GET /transfers` | `status` (`pending`, `confirmed`), `originAccountId` (int), `from` (datetime UTC), `to` (datetime UTC), `limit` (1-100) | "Historial de transferencias confirmadas enviadas desde la nómina" |
| `reconciliation.list` | `GET /reconciliation` | `status` (`pending`, `matched`) | "Transferencias pendientes por conciliar" |
| `statements.list` | `GET /accounts/{id}/statements` | `year` (int), `month` (int), `status` (`generated`, `archived`) | "Estados de cuenta del primer trimestre 2026" |
| `expenseCategories.list` | `GET /expense-categories` | `search` (texto: busca en nombre y código) | "Filtrar categorías que contengan 'comida'" |
| `budgets.monthly` | `GET /me/budgets/monthly` | `year` (int, req), `month` (int, req), `category` (código catálogo), `status` (`active`, `exceeded`) | "Presupuestos que ya se pasaron este mes" |
| `savingsGoals.list` | `GET /me/savings-goals` | `status` (`active`, `paused`, `completed`) | "Metas de ahorro que ya completé" |
| `creditCards.list` | `GET /me/credit-cards` | `status` (`active`, `blocked`) | "Mis tarjetas activas" |
| `creditCard.statements` | `GET /me/credit-cards/{id}/statements` | `year` (int), `month` (int) | "Estado de cuenta de la tarjeta de junio 2026" |
| `purchases.list` 🆕 | `GET /me/purchases` | `type` (`fisica`, `en_linea`, `recurrente`, `msi`), `from`, `to`, `cardId`, `merchant` | "Compras en línea de esta quincena" |

## 2. Enlace con la Personalización y Accesibilidad

1. **Lenguaje claro (`PlainLanguage`)**: cuando la IA detecta filtros activos, redacta el resumen contextual:
   - *Sin filtro*: "Tus movimientos recientes:"
   - *Con filtro de categoría y fecha*: "Tus gastos en Supermercados del 1 al 15 de junio suman {{filtered.total}}."
2. **Reducción de carga cognitiva**: los filtros permiten a la IA mostrar únicamente información relevante (ej. solo metas activas o solo presupuestos en riesgo), cumpliendo con los principios de diseño inclusivo WCAG 2.2.
3. **Persistencia de estado en UI**: los filtros se ligan a las `stateKeys` del contrato (`selectedDateRange`, `selectedAccountId`, `selectedCardId`), manteniendo consistencia entre vistas.

# 06 — Catálogo IA: qué puede consultar, placeholders y reglas

> Doc consumible por la IA (Guillermo / MCP). Fuente normativa: `contracts/a2ui/a2ui-mcp-contract.yaml`. Este archivo la resume en tablas y agrega placeholders y reglas de personalización. Si hay conflicto, manda el YAML.

## 6.1 Principios (del contrato)

1. La IA **solo emite `dataRef`** + estados `loading/error/fallback`. **Nunca** saldos, cuentas ni datos sensibles reales.
2. El frontend resuelve cada `dataRef` vía API (`http://localhost:8000`, `contracts/openapi/openapi.yaml`).
3. Fechas en UTC; el frontend convierte a local (`America/Mexico_City`).
4. `validation.rejectIf`: dataRef inexistente, dato sensible real, mutación sin confirmación, falta de `loading/error/fallback`.
5. `stateKeys`: `selectedAccountId`, `currentTransferId`, `selectedDateRange`, `selectedStatementId`, `selectedCardId`.

## 6.2 dataRefs disponibles (16 actuales + 3 propuestos)

| # | dataRef | Endpoint | Componente(s) | Datos que habilita |
|---|---|---|---|---|
| 1 | `server.time` | `GET /server-time` | — | hora oficial para periodos |
| 2 | `me.preferences` | `GET /me/preferences` | `AccessibilityPanel` | `fontScale, highContrast, darkMode, reducedMotion, largeTargets, plainLanguage` |
| 3 | `accounts.list` | `GET /accounts` | `AccountList` | alias, `maskedNumber`, saldo por cuenta |
| 4 | `accounts.summary.totalBalance` | `GET /me/account-summary` | `StatCard`, `StatLabel` | saldo total |
| 5 | `account.detail` | `GET /accounts/{accountId}` | — | detalle de cuenta |
| 6 | `transactions.list` | `GET /accounts/{accountId}/transactions` | `TransactionList` | descripción, monto, fecha, categoría (filtros: `from,to,category,expenseCategory,direction,status,search,limit`) |
| 6b 🆕 | `transactions.global` | `GET /me/transactions` | `TransactionList` | movimientos de todas las cuentas (mismos filtros + `accountId` opcional) |
| 7 | `dailyBalances.list` | `GET /accounts/{accountId}/daily-balances` | `DailyBalanceChart` | apertura/ingresos/egresos/cierre por día (filtros: `from,to`) |
| 8 | `transfer.detail` | `GET /transfers/{transferId}` | `TransferSummary` | alias destino, monto, estado |
| 8b 🆕 | `transfers.list` | `GET /transfers` | `TransferList` | historial de transferencias (filtros: `status,originAccountId,from,to,limit`) |
| 9 | `reconciliation.list` | `GET /reconciliation` | `ReconciliationTable` | matches + scores (filtro: `status`) |
| 10 | `statements.list` | `GET /accounts/{accountId}/statements` | `StatementList` | periodos, saldos, conteos (filtros: `year,month,status`) |
| 11 | `statements.expenses` | `GET …/statements/{statementId}` | `StatementSummary`, `ExpenseBreakdownChart` | totales + desglose por categoría |
| 12 | `expenseCategories.list` | `GET /expense-categories` | `CategoryList` | nombre, icono (filtro: `search`) |
| 13 | `budgets.monthly` | `GET /me/budgets/monthly` | `BudgetProgressCard` | límite, gastado, % avance (filtros: `year,month,category,status`) |
| 14 | `savingsGoals.list` | `GET /me/savings-goals` | `SavingsGoalCard` | nombre, % avance, restante (filtro: `status`) |
| 15 | `creditCards.list` | `GET /me/credit-cards` | `CreditCardSummary` | enmascarada, límite, disponible (filtro: `status`) |
| 16 | `creditCard.statements` | `GET /me/credit-cards/{cardId}/statements` | (reutiliza `StatementSummary`) | saldo anterior, pagos, compras, intereses, mínimo, vencimiento (filtros: `year,month`) |
| 17 🆕 | `purchases.list` | `GET /me/purchases` | `PurchaseList` | comercio, monto, fecha, tipo, MSI |
| 18 🆕 | `purchase.detail` | `GET /me/purchases/{id}` | — | detalle de una compra |
| 19 🆕 | `statement.purchases` | `GET …/statements/{id}/purchases` | `StatementPurchases` | line-items del periodo |

Acción disponible: `confirmTransfer` (`POST /transfers/{transferId}/confirm`, `requiresConfirmation:true`, idempotente por `IdempotencyKey`).

## 6.3 Placeholders por dataRef

| dataRef | Placeholders |
|---|---|
| `me.preferences` | `{{prefs.fontScale}}`, `{{prefs.highContrast}}`, `{{prefs.darkMode}}`, `{{prefs.reducedMotion}}`, `{{prefs.largeTargets}}`, `{{prefs.plainLanguage}}` |
| `accounts.*` | `{{user.firstName}}`, `{{account.alias}}`, `{{account.maskedNumber}}`, `{{account.balance}}`, `{{total.balance}}` |
| `transactions.list` | `{{tx.description}}`, `{{tx.amount}}`, `{{tx.date}}`, `{{tx.category}}` |
| `dailyBalances.list` | `{{balance.date}}`, `{{balance.closing}}` |
| `transfer.detail` | `{{transfer.alias}}`, `{{transfer.amount}}`, `{{transfer.status}}` |
| `reconciliation.list` | `{{recon.score}}`, `{{recon.status}}` |
| `statements.*` | `{{statement.period}}`, `{{statement.closing}}`, `{{statement.txCount}}`, `{{statement.topCategory}}`, `{{stmtExp.category}}`, `{{stmtExp.amount}}` |
| `budgets.monthly` | `{{budget.category}}`, `{{budget.limit}}`, `{{budget.spent}}`, `{{budget.progressPct}}` |
| `savingsGoals.list` | `{{goal.name}}`, `{{goal.progressPct}}`, `{{goal.remaining}}` |
| `creditCards.*` | `{{card.masked}}`, `{{card.available}}`, `{{cardStmt.minimum}}`, `{{cardStmt.dueDate}}`, `{{cardStmt.totalPurchases}}` |
| `purchases.*` 🆕 | `{{purchase.merchant}}`, `{{purchase.amount}}`, `{{purchase.type}}`, `{{purchase.installment}}`, `{{purchases.monthTotal}}` |

## 6.4 Reglas de personalización

| Señal | Adaptación |
|---|---|
| `plainLanguage=true` | Redactado simple: "Vas a enviar {{transfer.amount}} a {{transfer.alias}}" en vez de tecnicismos |
| `fontScale` | Escala tipográfica en todos los componentes con montos |
| `highContrast` / `darkMode` | Temas; estados nunca solo por color (texto + icono, WCAG 1.4.1) |
| `reducedMotion` | Sin animaciones en charts y celebraciones |
| `largeTargets` | Objetivos ≥ 24×24 CSS px (WCAG 2.5.8) en botones/enlaces de cada componente |
| `detected.*` (confianza alta) | Sugerir ajuste ("¿aumentamos la letra?"), nunca auto-aplicar |
| `user.locale` | Formato `es-MX`: `$24,829.25`, fechas `dd/mm/aaaa` |
| `statement.topCategory` / `budget.progressPct` | Mensajes proactivos ("Gastaste más en {{statement.topCategory}}", "Vas al {{budget.progressPct}} de tu súper") |
| `purchase.*` 🆕 | "Tus compras en línea suman {{purchases.onlineTotal}}"; alerta de MSI por terminar |

## 6.5 Lo que la IA NO puede (límites)

- Sin dataRef de `UserProfile`, `Session`, `MemoryEvent`, `DetectedPreference`, `AuditLog`: la personalización por comportamiento llega como **sugerencia agregada**, nunca como eventos crudos.
- Sin escritura salvo `confirmTransfer` (con confirmación). Las compras las crea el banco: la IA solo las lee.
- Sin `PasswordHash`, números de cuenta/tarjeta completos ni payloads sin redactar.

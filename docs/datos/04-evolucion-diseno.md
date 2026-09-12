# 04 — Evolución del diseño en git

Historia de la base de datos a través de los commits: plan original, lo agregado después y las brechas que quedaron. Decisiones formales en `../arquitectura/adrs/`.

## 4.1 Commit `7a56250` — plan original (13 tablas, migración `InitialCreate`)

Núcleo bancario + identidad + memoria de accesibilidad:

| Bloque | Tablas | Intención |
|---|---|---|
| Identidad | `Users`, `UserProfiles`, `Sessions`, `AuditLogs` | auth, perfil demográfico, sesiones, trazabilidad |
| Accesibilidad | `AccessibilityPreferences`, `DetectedPreferences`, `MemoryEvents` | ajustes explícitos + detección por comportamiento (redactado, con `RetentionUntil`) |
| Cuentas | `Accounts`, `Transactions`, `DailyBalances` | ledger + foto diaria para gráficas |
| Transferencias | `Transfers` (idempotente), `TransferConfirmations`, `ReconciliationMatches` | dos pasos + conciliación con score |

Lo que el plan original **no** incluía: categorías de gasto, statements, presupuestos, metas, tarjetas ni compras. `Transaction.Category` era string libre (`nomina`, `super`…).

## 4.2 Commit `2cfc9d7` — finanzas personales (7 tablas, migración `StatementsBudgetsGoalsCards`)

| Cambio | Detalle |
|---|---|
| `ExpenseCategories` (nueva) | catálogo (`Code` único, 10 seed); `Transaction.IdExpenseCategory?` (setnull) para clasificar sin romper historial |
| `Statements` + `StatementExpenses` (nuevas) | estado de débito idempotente por (`IdAccount`, `PeriodStart`) + agregado por categoría; `StatementService` + job diario `StatementGenerationService` |
| `Budgets` (nueva) | tope mensual único por usuario+categoría+mes+año; `SyncFromStatementAsync` lo alimenta |
| `SavingsGoals` (nueva) | metas con aporte y auto-`completed` |
| `CreditCards` + `CreditCardStatements` (nuevas) | tarjeta + statement 1-1 con `Statement` base (`AccountType=credito`); `TotalPurchases` como **parámetro manual** |
| `User` / `Account` | nuevas navegaciones (`Budgets`, `SavingsGoals`, `CreditCards`, `Statements`) |

## 4.3 Brechas que quedaron (→ `05-brechas-compras.md`)

1. **Compras del usuario**: no hay tabla; el único rastro es `CreditCardStatement.TotalPurchases` (agregado, manual). Decisión tomada: **nueva entidad `Purchase`** (ADR-001).
2. **Tipo de compra**: sin vocabulario controlado. Decisión tomada: **enum en código** `fisica|en_linea|recurrente|msi` (ADR-002).
3. **Line-items de statements**: `StatementExpense` agrega por categoría pero no hay detalle por compra. Decisión tomada: **documentar lo existente + proponer `Purchase.IdStatement`** (ADR-003).

## 4.4 ADRs

| ADR | Decisión | Estado |
|---|---|---|
| [ADR-001](../arquitectura/adrs/ADR-001-entidad-purchase.md) | Compras como nueva entidad `Purchase` | Aceptado (diseño, sin implementar) |
| [ADR-002](../arquitectura/adrs/ADR-002-purchasetype-enum.md) | Tipo de compra como enum, no tabla | Aceptado (diseño, sin implementar) |
| [ADR-003](../arquitectura/adrs/ADR-003-statement-line-items.md) | Statements existentes + line-items vía `Purchase.IdStatement`; `TotalPurchases` calculado | Aceptado (diseño, sin implementar) |

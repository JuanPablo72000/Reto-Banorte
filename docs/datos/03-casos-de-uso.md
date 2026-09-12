# 03 — Casos de uso y matriz de datos

Cada caso de uso indica: entidades que lee/escribe, endpoints, `dataRef` que la IA puede usar, componentes A2UI y placeholders para interfaces personalizadas.

> Leyenda IA: ✅ consultable vía dataRef · ✏️ acción confirmada · 🔒 solo backend · 🆕 propuesto (`Purchase`).

## CU-01 Registro y login

| Aspecto | Detalle |
|---|---|
| Lee / escribe | Lee `User` (por `Email`); escribe `User` + `AccessibilityPreference` (defaults) |
| Endpoints | `POST /auth/register` → 201 · `POST /auth/login` |
| IA | 🔒 (anon). Tras login, saludo con `AuthResponse.UserDto` |
| Placeholders | `{{user.firstName}}` ("Hola, {{user.firstName}}"), `{{user.locale}}` |
| Personalización | `Locale=es-MX` define formato moneda/fecha y redactado (`PlainLanguage`) |

## CU-02 Ver cuentas y saldo total

| Aspecto | Detalle |
|---|---|
| Lee | `User` → `Accounts` (+ `CreditCards` para el total) |
| Endpoints | `GET /accounts` · `GET /accounts/{id}` · `GET /me/account-summary` |
| IA | ✅ `accounts.list` (`AccountList`) · `account.detail` · `accounts.summary.totalBalance` (`StatCard`, `StatLabel`) |
| Placeholders | `{{account.alias}}`, `{{account.maskedNumber}}`, `{{account.balance}}`, `{{total.balance}}` |
| Personalización | Mostrar `Alias` + `MaskedNumber` (nunca número completo); `FontScale`/`LargeTargets` en tarjetas; ejemplo contractual `total-balance`, `account-list` |

## CU-03 Ver movimientos y su evolución

| Aspecto | Detalle |
|---|---|
| Lee | `Account` → `Transactions` (filtros `from,to,category,direction,status,search,limit`) + `DailyBalances` |
| Endpoints | `GET /accounts/{id}/transactions` · `GET /accounts/{id}/daily-balances` |
| IA | ✅ `transactions.list` (`TransactionList`) · `dailyBalances.list` (`DailyBalanceChart`) |
| Placeholders | `{{tx.description}}`, `{{tx.amount}}`, `{{tx.date}}`, `{{tx.category}}`, `{{balance.date}}`, `{{balance.closing}}` |
| Personalización | Preferir `ExpenseCategory.Name` sobre `Category` libre; `ReducedMotion` desactiva la animación del chart; ejemplo contractual `transaction-list` |

## CU-03c Mis compras por tipo (🆕 con `Purchase`)

| Aspecto | Detalle |
|---|---|
| Lee | `Purchase` por usuario/cuenta/tarjeta, filtro `PurchaseType` (`fisica/en_linea/recurrente/msi`) |
| Endpoints | 🆕 `GET /me/purchases?type=&from=&to=` · `GET /me/credit-cards/{id}/purchases` |
| IA | 🆕 `purchases.list` (`PurchaseList`) |
| Placeholders | `{{purchase.merchant}}`, `{{purchase.amount}}`, `{{purchase.date}}`, `{{purchase.type}}`, `{{purchase.installment}}` ("3 de 12 MSI") |
| Personalización | "Tus compras en línea este mes suman {{purchases.onlineTotal}}"; alerta MSI próximos a terminar |

## CU-04 Transferir con confirmación

| Aspecto | Detalle |
|---|---|
| Escribe | `Transfer` (idempotente por `IdempotencyKey`) → `TransferConfirmation` → `ConfirmedAt`; auditoría `transfer.confirm` en `AuditLog` |
| Endpoints | `POST /transfers/` · `GET /transfers/{id}` · `POST /transfers/{id}/confirm` |
| IA | ✅ `transfer.detail` (`TransferSummary`, solo lectura) · ✏️ acción `confirmTransfer` (`requiresConfirmation:true`) |
| Placeholders | `{{transfer.alias}}` (`DestinationAlias`), `{{transfer.amount}}`, `{{transfer.status}}` |
| Personalización | Resumen en lenguaje simple si `PlainLanguage` ("Vas a enviar {{transfer.amount}} a {{transfer.alias}}"); foco visible en el botón de confirmar (WCAG 2.4.11) |

## CU-05 Conciliación transferencia ↔ movimiento

| Aspecto | Detalle |
|---|---|
| Lee | `ReconciliationMatch` + `Transfer` + `Transaction` |
| Endpoints | `GET /reconciliation` |
| IA | ✅ `reconciliation.list` (`ReconciliationTable`) |
| Placeholders | `{{recon.score}}`, `{{recon.status}}`, `{{recon.transfer}}`, `{{recon.transaction}}` |
| Personalización | Explicar el score en lenguaje simple ("coincide por monto y fecha"); estados con texto, no solo color (WCAG 1.4.1) |

## CU-06 Estado de cuenta de débito

| Aspecto | Detalle |
|---|---|
| Lee / escribe | Genera `Statement` idempotente por (`IdAccount`, `PeriodStart`) desde `Transactions` del periodo + `StatementExpenses` por categoría; dispara `BudgetService.SyncFromStatementAsync`; job diario `StatementGenerationService` |
| Endpoints | `POST /accounts/{id}/statements/generate` · `GET /accounts/{id}/statements` · `GET …/statements/{statementId}` |
| IA | ✅ `statements.list` (`StatementList`) · `statements.expenses` (`StatementSummary`, `ExpenseBreakdownChart`) |
| Placeholders | `{{statement.period}}`, `{{statement.opening}}`, `{{statement.closing}}`, `{{statement.txCount}}`, `{{statement.topCategory}}`, `{{stmtExp.category}}`, `{{stmtExp.amount}}` |
| Personalización | "En {{statement.period}} gastaste más en {{statement.topCategory}}: {{stmtExp.amount}}"; gráfica con alternativa textual (WCAG 1.1.1) |

## CU-06b Detalle de compras del periodo (🆕 con `Purchase`)

| Aspecto | Detalle |
|---|---|
| Lee | `Statement` → `Purchases` (`IdStatement`) ordenadas por fecha |
| Endpoints | 🆕 `GET /accounts/{id}/statements/{statementId}/purchases` |
| IA | 🆕 `statement.purchases` (`StatementPurchases`) |
| Placeholders | `{{purchase.merchant}}`, `{{purchase.type}}`, `{{purchase.installment}}` |
| Personalización | Agrupar por `PurchaseType`; MSI con progreso de parcialidades |

## CU-07 Estado de cuenta de tarjeta de crédito

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `CreditCard` → `CreditCardStatement` + `Statement` base (`AccountType=credito`, 1-1); `GenerateStatementAsync` recibe `totalPurchases/totalPayments` como parámetros (hoy no se calculan del ledger) |
| Endpoints | `GET /me/credit-cards/{cardId}/statements` · `POST …/statements/generate` |
| IA | ✅ `creditCard.statements` (reutiliza `StatementSummary`) |
| Placeholders | `{{cardStmt.previous}}`, `{{cardStmt.payments}}`, `{{cardStmt.totalPurchases}}`, `{{cardStmt.interests}}`, `{{cardStmt.minimum}}`, `{{cardStmt.dueDate}}` |
| Personalización | "Tu pago mínimo es {{cardStmt.minimum}} con vencimiento {{cardStmt.dueDate}}"; 🆕 con `Purchase`: el total se calcula de line-items y el desglose sustituye al parámetro manual |

## CU-08 Presupuestos mensuales

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `Budget` único por usuario+categoría+mes+año; `CurrentSpent` sincronizado desde `Statement`; resumen mensual agregado |
| Endpoints | `POST /me/budgets/` · `GET /me/budgets/monthly?year&month` · `DELETE /me/budgets/{id}` |
| IA | ✅ `budgets.monthly` (`BudgetProgressCard`) |
| Placeholders | `{{budget.category}}`, `{{budget.limit}}`, `{{budget.spent}}`, `{{budget.progressPct}}` |
| Personalización | "Vas al {{budget.progressPct}} de tu presupuesto de {{budget.category}}"; barra con texto alternativo, no solo color |

## CU-09 Metas de ahorro

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `SavingsGoal`; `ContributeAsync` acumula y auto-`completed`; `SetStatusAsync` (`active/paused/completed`); borrado |
| Endpoints | `POST /me/savings-goals/` · `GET /me/savings-goals/` · `POST …/{id}/contribute` · `PUT …/{id}/status` · `DELETE …/{id}` |
| IA | ✅ `savingsGoals.list` (`SavingsGoalCard`) |
| Placeholders | `{{goal.name}}`, `{{goal.progressPct}}`, `{{goal.remaining}}`, `{{goal.targetDate}}` |
| Personalización | "Te faltan {{goal.remaining}} para {{goal.name}}"; celebrar `completed` con mensaje + `ReducedMotion`-safe (sin confeti animado si está activo) |

## CU-10 Tarjetas (resumen y cargos)

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `CreditCard` (crear, listar); `PayAsync` aplica pago y audita `credit-card.pay` |
| Endpoints | `POST /me/credit-cards` · `GET /me/credit-cards` · `POST …/{id}/pay` |
| IA | ✅ `creditCards.list` (`CreditCardSummary`) |
| Placeholders | `{{card.masked}}`, `{{card.type}}`, `{{card.limit}}`, `{{card.available}}` |
| Personalización | Mostrar siempre enmascarada; 🆕 `Purchase` permite "compras a MSI activas: N" |

## CU-11 Pagar tarjeta

| Aspecto | Detalle |
|---|---|
| Escribe | `CreditCard.AvailableCredit` + `AuditLog(credit-card.pay)` |
| Endpoints | `POST /me/credit-cards/{id}/pay` |
| IA | ✏️ (acción futura; hoy solo lectura vía `creditCards.list`) |
| Personalización | Confirmación con monto en palabras si `PlainLanguage` |

## CU-12 Preferencias de accesibilidad y perfil

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `AccessibilityPreference` (get/update) + `UserProfile` (`Age`, `DisabilityType`) |
| Endpoints | `GET /users/me` · `GET /me/preferences/` · `PUT /me/preferences/` |
| IA | ✅ `me.preferences` (`AccessibilityPanel`) · `GET /server-time` (`server.time`) para fechas |
| Placeholders | `{{prefs.fontScale}}`, `{{prefs.highContrast}}`, `{{prefs.darkMode}}`, `{{prefs.reducedMotion}}`, `{{prefs.largeTargets}}`, `{{prefs.plainLanguage}}` |
| Personalización | Sugerir valores iniciales desde `DisabilityType` (ej. `visual` → `FontScale` 1.25 + `HighContrast`); ver `../accesibilidad/wcag22-aa.md` |

## CU-13 Detección de necesidades por comportamiento

| Aspecto | Detalle |
|---|---|
| Lee / escribe | `Session` → `MemoryEvents` (redactados, con `RetentionUntil`) → agregan `DetectedPreference` (`ConfidenceScore`, `BasedOnEventsCount`) |
| Endpoints | 🔒 (motor interno, sin endpoints públicos) |
| IA | Indirecto: propone adaptar UI ("¿aumentamos la letra?") citando evidencia agregada, nunca eventos crudos |
| Placeholders | `{{detected.suggestion}}`, `{{detected.confidence}}` |
| Personalización | Solo sugerir, nunca auto-aplicar cambios irreversibles; respetar `RetentionUntil` (privacidad) |

## Matriz resumen

| CU | Entidades | Endpoint(s) | dataRef | Componente(s) |
|---|---|---|---|---|
| 01 | User, AccessibilityPreference | `/auth/*` | — (anon) | — |
| 02 | User, Account, CreditCard | `/accounts`, `/me/account-summary` | `accounts.list`, `account.detail`, `accounts.summary.totalBalance` | AccountList, StatCard, StatLabel |
| 03 | Account, Transaction, DailyBalance, ExpenseCategory | `…/transactions`, `…/daily-balances` | `transactions.list`, `dailyBalances.list` | TransactionList, DailyBalanceChart |
| 03c 🆕 | Purchase | `/me/purchases` | `purchases.list` | PurchaseList |
| 04 | Transfer, TransferConfirmation, AuditLog | `/transfers/*` | `transfer.detail` + acción `confirmTransfer` | TransferSummary |
| 05 | ReconciliationMatch, Transfer, Transaction | `/reconciliation` | `reconciliation.list` | ReconciliationTable |
| 06 | Statement, StatementExpense, Transaction, Budget | `…/statements*` | `statements.list`, `statements.expenses` | StatementList, StatementSummary, ExpenseBreakdownChart |
| 06b 🆕 | Statement, Purchase | `…/statements/{id}/purchases` | `statement.purchases` | StatementPurchases |
| 07 | CreditCard, CreditCardStatement, Statement | `/me/credit-cards/*/statements*` | `creditCard.statements` | StatementSummary |
| 08 | Budget, ExpenseCategory | `/me/budgets*` | `budgets.monthly` | BudgetProgressCard |
| 09 | SavingsGoal | `/me/savings-goals*` | `savingsGoals.list` | SavingsGoalCard |
| 10 | CreditCard | `/me/credit-cards` | `creditCards.list` | CreditCardSummary |
| 11 | CreditCard, AuditLog | `…/pay` | — (acción futura) | — |
| 12 | AccessibilityPreference, UserProfile | `/me/preferences/*`, `/users/me` | `me.preferences`, `server.time` | AccessibilityPanel |
| 13 | Session, MemoryEvent, DetectedPreference | — (interno) | — | — |

# 02 — Catálogo de entidades

Ficha por entidad: propósito, campos (tipos y restricciones verificados en `Models/*.cs`), relaciones con `DeleteBehavior`, reglas de negocio, casos de uso (→ `03-casos-de-uso.md`), exposición a la IA (endpoint + `dataRef` del contrato A2UI) y placeholders que habilita.

> Convención: `IA: sí (dataRef)` = la IA puede referenciarla vía placeholder; `IA: no` = solo backend.

---

## 2.1 User

**Propósito**: identidad del cliente. Raíz de casi todos los agregados.

| Campo | Tipo | Notas |
|---|---|---|
| `IdUser` | int PK | |
| `Name` | string(120) requerido | → `{{user.firstName}}`, saludo personalizado |
| `Email` | string(160), único | login |
| `PasswordHash` | string BCrypt | **nunca en DTOs** |
| `Locale` | string(10), default `es-MX` | formato fecha/moneda, lenguaje simple |
| `Status` | string(20), default `active` | |
| `CreatedAt` | DateTime UTC | |

**Relaciones**: 1-1 `UserProfile`, `AccessibilityPreference` (cascade); 1-N `Sessions`, `MemoryEvents` (restrict), `DetectedPreferences`, `Accounts`, `Transfers`, `AuditLogs`, `Budgets`, `SavingsGoals`, `CreditCards` (cascade).
**Casos de uso**: CU-01 registro/login, CU-12 perfil y personalización.
**IA**: sí — `GET /users/me` → `me.preferences` (parcial: preferencias) y saludo vía `AuthResponse.UserDto`. Placeholders: `{{user.firstName}}`, `{{user.locale}}`.

## 2.2 UserProfile

**Propósito**: datos demográficos para adaptar la experiencia (no autenticación).

| Campo | Tipo | Notas |
|---|---|---|
| `IdProfile` | int PK | |
| `IdUser` | int FK único → `User` | 1-1 cascade |
| `Age` | int | adaptar tamaño/complejidad |
| `DisabilityType` | string(60) | ej. `visual`; sugiere ajustes iniciales |
| `UpdatedAt` | DateTime UTC | |

**Casos de uso**: CU-12 (sugerir `LargeTargets`/`PlainLanguage` según `DisabilityType`).
**IA**: indirecto — alimenta la personalización inicial. Placeholders: `{{user.disabilityType}}` (solo para adaptar UI, nunca mostrar como etiqueta).

## 2.3 AccessibilityPreference

**Propósito**: ajustes explícitos de accesibilidad del usuario. Base de la personalización UI.

| Campo | Tipo | Notas |
|---|---|---|
| `IdPreference` | int PK | |
| `IdUser` | int FK único → `User` | 1-1 cascade |
| `FontScale` | float, default 1.0 | escala tipográfica (seed demo 1.25) |
| `HighContrast` | bool | tema de contraste |
| `DarkMode` | bool | |
| `ReducedMotion` | bool | desactiva animaciones |
| `LargeTargets` | bool | objetivos táctiles ≥ 24px (WCAG 2.2 AA 2.5.8) |
| `PlainLanguage` | bool | redactado simple en IA/UI |
| `UpdatedAt` | DateTime UTC | |

**Casos de uso**: CU-12, CU-13 (detección implícita que propone actualizar estos valores).
**IA**: sí — `GET /me/preferences/` → `me.preferences` → componente `AccessibilityPanel`. Placeholders: `{{prefs.fontScale}}`, `{{prefs.highContrast}}`, etc. Ver `../accesibilidad/wcag22-aa.md`.

## 2.4 Session

**Propósito**: agrupar la actividad del usuario por sesión/dispositivo para el motor de memoria.

| Campo | Tipo | Notas |
|---|---|---|
| `IdSession` | int PK | |
| `IdUser` | int FK → `User` | N-1 cascade |
| `StartedAt` / `EndedAt?` | DateTime UTC | `EndedAt` null = sesión abierta |
| `DeviceContext` | string(200) | ej. `web`; permite adaptar por dispositivo |

**Relaciones**: 1-N `MemoryEvents` (cascade).
**Casos de uso**: CU-13 (contexto de eventos de comportamiento).
**IA**: no expuesta (interna del motor de memoria).

## 2.5 MemoryEvent

**Propósito**: evento de comportamiento (ej. `zoom` sobre `balance-card`) con resumen **redactado**. Materia prima para detectar preferencias.

| Campo | Tipo | Notas |
|---|---|---|
| `IdEvent` | int PK | |
| `IdSession` | int FK → `Session` | cascade |
| `IdUser` | int FK → `User` | **restrict** (conserva evidencia aunque se borre sesión) |
| `IdDetectedPreference?` | int FK nullable → `DetectedPreference` | setnull |
| `EventType` | string(60) | ej. `zoom` |
| `Intent` | string(120) | ej. `aumentar-legibilidad` |
| `TargetElement` | string(120) | ej. `balance-card`; la IA sabe qué piezas se usan |
| `RedactedSummary` | string(500) | sin datos sensibles |
| `SensitivityLevel` | string(10), default `low` | |
| `CreatedAt` / `RetentionUntil?` | DateTime UTC | caducidad de privacidad (seed: 90 días) |

**Casos de uso**: CU-13.
**IA**: no expuesta como dato; sus agregados (`DetectedPreference`) sí alimentan personalización.

## 2.6 DetectedPreference

**Propósito**: preferencia inferida del comportamiento con nivel de confianza.

| Campo | Tipo | Notas |
|---|---|---|
| `IdDetected` | int PK | |
| `IdUser` | int FK → `User` | cascade |
| `PreferenceType` | string(60) | ej. `fontScale` |
| `Value` | string(200) | ej. `1.25` |
| `ConfidenceScore` | float | ej. 0.87; umbral para sugerir al usuario |
| `BasedOnEventsCount` | int | evidencia (ej. 5) |
| `UpdatedAt` | DateTime UTC | |

**Relaciones**: 1-N `MemoryEvents`.
**Casos de uso**: CU-13 (sugerir "¿aumentamos el tamaño de letra?" en lenguaje simple si `PlainLanguage`).
**IA**: indirecto — justifica adaptaciones proactivas. Placeholder: `{{detected.suggestion}}`.

## 2.7 Account

**Propósito**: cuenta del usuario (débito / crédito como cuenta contable). Centro del dominio bancario.

| Campo | Tipo | Notas |
|---|---|---|
| `IdAccount` | int PK | → `stateKeys.selectedAccountId` |
| `IdUser` | int FK → `User` | cascade |
| `AccountType` | string(30) | `debito` / `credito` |
| `Alias` | string(60) | ej. `Nómina`; mostrar en lugar de números |
| `MaskedNumber` | string(20) | ej. `****1234`; nunca número completo |
| `Currency` | string(5), default `MXN` | |
| `Balance` | decimal(18,2) | saldo consultable |
| `Status` | string(20), default `active` | |
| `CreatedAt` | DateTime UTC | |

**Relaciones**: 1-N `Transactions`, `DailyBalances`, `Statements` (cascade); 1-N `Transfers` como origen (**restrict**: no borrar cuenta con transferencias).
**Casos de uso**: CU-02 (listar/resumir), CU-03 (movimientos), CU-04 (transferir), CU-06/07 (statements).
**IA**: sí — `GET /accounts` → `accounts.list` (`AccountList`); `GET /accounts/{id}` → `account.detail`; `GET /me/account-summary` → `accounts.summary.totalBalance` (`StatCard`/`StatLabel`). Placeholders: `{{account.alias}}`, `{{account.maskedNumber}}`, `{{account.balance}}`, `{{total.balance}}`.

## 2.8 Transaction

**Propósito**: movimiento del ledger de una cuenta. Grano más fino consultable hoy.

| Campo | Tipo | Notas |
|---|---|---|
| `IdTransaction` | int PK | |
| `IdAccount` | int FK → `Account` | cascade |
| `Date` | DateOnly | |
| `Amount` | decimal(18,2) | signo por `Direction` |
| `Direction` | string(10) | `credit` / `debit` |
| `Category` | string(40) | texto libre (`nomina`, `super`) — legado, preferir `ExpenseCategory` |
| `Description` | string(200) | ej. `Súper` |
| `Status` | string(20) | `posted`… |
| `Reference` | string(60) | ej. `SUP-002` |
| `IdExpenseCategory?` | int FK nullable → `ExpenseCategory` | setnull |

**Relaciones**: 1-1 `ReconciliationMatch` (cascade); N-1 `ExpenseCategory`.
**Casos de uso**: CU-03 (listar/filtrar: `from,to,category,direction,status,search,limit`), CU-05 (conciliación), CU-06 (insumo del statement).
**IA**: sí — `GET /accounts/{id}/transactions` → `transactions.list` (`TransactionList`). Placeholders: `{{tx.description}}`, `{{tx.amount}}`, `{{tx.date}}`, `{{tx.category}}`.
**Límite conocido**: no guarda comercio ni tipo de compra → ver `Purchase` (2.20).

## 2.9 DailyBalance

**Propósito**: foto diaria agregada para gráficas sin recalcular el ledger.

| Campo | Tipo | Notas |
|---|---|---|
| `IdBalance` | int PK | |
| `IdAccount` | int FK → `Account` | cascade; único (`IdAccount`, `Date`) |
| `Date` | DateOnly | |
| `OpeningBalance` / `Income` / `Expenses` / `ClosingBalance` | decimal(18,2) | |

**Casos de uso**: CU-03b (gráfica de evolución).
**IA**: sí — `GET /accounts/{id}/daily-balances` → `dailyBalances.list` (`DailyBalanceChart`). Placeholders: `{{balance.date}}`, `{{balance.closing}}`.

## 2.10 Transfer

**Propósito**: transferencia entre cuentas con idempotencia y confirmación en dos pasos.

| Campo | Tipo | Notas |
|---|---|---|
| `IdTransfer` | int PK | → `stateKeys.currentTransferId` |
| `IdUser` | int FK → `User` | cascade |
| `IdOriginAccount` | int FK → `Account` | **restrict** |
| `DestinationAlias` | string(60) | ej. `Mamá` |
| `DestinationMasked` | string(20) | `****5678` |
| `Amount` / `Currency` | decimal / string(5)=MXN | |
| `Concept` | string(140) | |
| `Status` | string(20), default `pending` | `pending` → confirmada |
| `IdempotencyKey` | string(80) único, default Guid | reintentos seguros |
| `ConfirmedAt?` | DateTime UTC nullable | |

**Relaciones**: 1-N `TransferConfirmations` (cascade); 1-1 `ReconciliationMatch` (cascade).
**Casos de uso**: CU-04 (crear, consultar, confirmar).
**IA**: sí (lectura) + 1 acción — `GET /transfers/{id}` → `transfer.detail` (`TransferSummary`); `POST …/confirm` → acción `confirmTransfer` (`requiresConfirmation:true`). Placeholders: `{{transfer.alias}}`, `{{transfer.amount}}`, `{{transfer.status}}`.

## 2.11 TransferConfirmation

**Propósito**: evidencia de cada intento/confirmación de una transferencia.

| Campo | Tipo | Notas |
|---|---|---|
| `IdConfirmation` | int PK | |
| `IdTransfer` | int FK → `Transfer` | cascade |
| `Method` | string(30) | ej. `app` |
| `Status` | string(20), default `pending` | |
| `ConfirmedAt?` | DateTime UTC nullable | |

**Casos de uso**: CU-04 (auditoría del segundo factor).
**IA**: incluida en `transfer.detail`; sin dataRef propio.

## 2.12 ReconciliationMatch

**Propósito**: vínculo 1-1 entre `Transfer` y su `Transaction` contable, con score.

| Campo | Tipo | Notas |
|---|---|---|
| `IdMatch` | int PK | |
| `IdTransfer` | int FK único → `Transfer` | cascade |
| `IdTransaction` | int FK único → `Transaction` | cascade |
| `Status` | string(20), default `pending` | |
| `MatchScore` | float | |
| `MatchedAt?` | DateTime UTC nullable | |
| `Notes` | string(300) | |

**Casos de uso**: CU-05 (tabla de conciliación).
**IA**: sí — `GET /reconciliation` → `reconciliation.list` (`ReconciliationTable`). Placeholders: `{{recon.score}}`, `{{recon.status}}`.

## 2.13 AuditLog

**Propósito**: trazabilidad de acciones sensibles con payload redactado.

| Campo | Tipo | Notas |
|---|---|---|
| `IdLog` | int PK | |
| `IdUser` | int FK → `User` | cascade |
| `Action` / `Resource` | string(60) | ej. `transfer.confirm`, `credit-card.pay` |
| `Result` | string(20) | `ok`… |
| `RiskLevel` | string(10), default `low` | |
| `RedactedPayload` | string(1000) | sin PII |
| `CreatedAt` | DateTime UTC | |

**Casos de uso**: transversal (CU-04, CU-11 generan auditoría).
**IA**: no expuesta.

## 2.14 ExpenseCategory

**Propósito**: catálogo de categorías de gasto. Eje de clasificación y personalización financiera.

| Campo | Tipo | Notas |
|---|---|---|
| `IdCategory` | int PK | |
| `Name` | string(60) | ej. `Supermercados` |
| `Code` | string(30) único | `gas`, `restaurant`, `supermarket`, `transport`… (10 seed) |
| `Icon` | string(40) | clave de icono (`cart`, `fuel`…) |
| `IsDefault` | bool | |
| `SortOrder` | int | orden de UI |

**Relaciones**: 1-N `Transactions` (setnull), `StatementExpenses` y `Budgets` (**restrict**: no borrar categoría en uso).
**Casos de uso**: CU-03, CU-06, CU-08, CU-09.
**IA**: sí — `GET /expense-categories` → `expenseCategories.list` (`CategoryList`). Placeholders: `{{category.name}}`, `{{category.icon}}`. Patrón de referencia para el enum `PurchaseType` (decisión: enum, no tabla — ver ADR-002).

## 2.15 Statement

**Propósito**: estado de cuenta de débito por periodo (`CutOffDay`, `PeriodStart/End`), idempotente por (`IdAccount`, `PeriodStart`).

| Campo | Tipo | Notas |
|---|---|---|
| `IdStatement` | int PK | → `stateKeys.selectedStatementId` |
| `IdAccount` | int FK → `Account` | cascade |
| `CutOffDay` | int | día de corte; `StatementService.StatementPeriod.Resolve` ajusta fin de mes |
| `PeriodStart` / `PeriodEnd` | DateOnly | |
| `OpeningBalance` / `ClosingBalance` / `TotalCredits` / `TotalDebits` | decimal(18,2) | |
| `TransactionCount` | int | |
| `AccountType` | string(30) | `debito` / `credito` (los base de tarjeta usan `credito`) |
| `Status` | string(20), default `generated` | |
| `GeneratedAt` | DateTime UTC | generación diaria 00:00 (`StatementGenerationService`) |

**Relaciones**: 1-N `StatementExpenses` (cascade); 1-1 `CreditCardStatement` (cascade, lado tarjeta).
**Casos de uso**: CU-06 (generar/listar/detalle). Al generar dispara `BudgetService.SyncFromStatementAsync`.
**IA**: sí — `GET …/statements` → `statements.list` (`StatementList`); `GET …/statements/{id}` → `statements.expenses` (`StatementSummary` + `ExpenseBreakdownChart`). Placeholders: `{{statement.period}}`, `{{statement.closing}}`, `{{statement.topCategory}}`, `{{statement.txCount}}`.
**Límite conocido**: sin line-items por compra → propuesta en 2.20 y `05-brechas-compras.md`.

## 2.16 StatementExpense

**Propósito**: agregado por categoría dentro de un statement. Insumo de gráficas y presupuestos.

| Campo | Tipo | Notas |
|---|---|---|
| `IdStatementExpense` | int PK | |
| `IdStatement` | int FK → `Statement` | cascade; único (`IdStatement`, `IdExpenseCategory`) |
| `IdExpenseCategory` | int FK → `ExpenseCategory` | **restrict** |
| `Amount` | decimal(18,2) | |
| `TransactionCount` | int | |
| `FirstTransactionDate?` / `LastTransactionDate?` | DateOnly nullable | rango de la categoría en el periodo |

**Casos de uso**: CU-06, CU-08.
**IA**: incluido en `statements.expenses`. Placeholders: `{{stmtExp.category}}`, `{{stmtExp.amount}}`, `{{stmtExp.count}}`.

## 2.17 Budget

**Propósito**: tope mensual por categoría. Único por (`IdUser`, `IdExpenseCategory`, `Month`, `Year`).

| Campo | Tipo | Notas |
|---|---|---|
| `IdBudget` | int PK | |
| `IdUser` / `IdExpenseCategory` | FK → `User` (cascade) / `ExpenseCategory` (**restrict**) | |
| `Month` / `Year` | int | |
| `AmountLimit` / `CurrentSpent` | decimal(18,2) | `CurrentSpent` se sincroniza desde el statement |
| `StartDate` / `EndDate` | DateTime UTC | |
| `Status` | string(20), default `active` | |
| `CreatedAt` / `UpdatedAt` | DateTime UTC | |

**Casos de uso**: CU-08 (crear/actualizar, resumen mensual, borrar; sync idempotente desde statement).
**IA**: sí — `GET /me/budgets/monthly` → `budgets.monthly` (`BudgetProgressCard`). Placeholders: `{{budget.category}}`, `{{budget.limit}}`, `{{budget.spent}}`, `{{budget.progressPct}}`, `{{budget.status}}` (ej. "vas al 70% de tu súper").

## 2.18 SavingsGoal

**Propósito**: meta de ahorro con aportaciones; auto-`completed` al alcanzar el objetivo.

| Campo | Tipo | Notas |
|---|---|---|
| `IdGoal` | int PK | |
| `IdUser` | int FK → `User` | cascade |
| `Name` | string(100) | ej. `Fondo de emergencia` → `{{goal.name}}` |
| `TargetAmount` / `CurrentAmount` | decimal(18,2) | |
| `TargetDate` | DateTime UTC | |
| `Status` | string(20), default `active` | `active`/`paused`/`completed` |
| `CreatedAt` / `UpdatedAt` | DateTime UTC | |

**Casos de uso**: CU-09 (crear, listar, aportar, pausar/completar, eliminar).
**IA**: sí — `GET /me/savings-goals` → `savingsGoals.list` (`SavingsGoalCard`). Placeholders: `{{goal.name}}`, `{{goal.progressPct}}`, `{{goal.remaining}}` ("te faltan $X para tu fondo").

## 2.19 CreditCard + 2.19b CreditCardStatement

**Propósito**: tarjeta de crédito del usuario y su estado de cuenta mensual.

`CreditCard`: `IdCreditCard` PK; `IdUser` FK cascade; `CardNumberMasked`(20) (solo `****5678`); `CardType`(20) (`Visa`…); `CreditLimit`, `AvailableCredit` decimal; `InterestRate`; `StatementCutOffDay`, `PaymentDueDay`; `Status` default `active`; `CreatedAt`.
Relación: 1-N `CreditCardStatements` (cascade).

`CreditCardStatement`: `IdCreditCardStatement` PK; `IdCreditCard` FK cascade; `IdStatement` FK único → `Statement` (1-1 cascade — el statement base es `AccountType=credito`); `PreviousBalance`, `TotalPayments`, `TotalCredits`, **`TotalPurchases`** (agregado mensual, sin desglose), `InterestCharges`, `MinimumPayment`, `AvailableCredit`; `PaymentDueDate` DateOnly; `Status` default `generated`; `GeneratedAt`.
**Casos de uso**: CU-10, CU-11 (crear, listar, generar statement con `totalPurchases/totalPayments` como parámetros, pagar con auditoría `credit-card.pay`).
**IA**: sí — `GET /me/credit-cards` → `creditCards.list` (`CreditCardSummary`); `GET …/{cardId}/statements` → `creditCard.statements`. Placeholders: `{{card.masked}}`, `{{card.available}}`, `{{cardStmt.minimum}}`, `{{cardStmt.dueDate}}`, `{{cardStmt.totalPurchases}}`.

## 2.20 Purchase (PROPUESTO — no existe en código)

**Propósito**: compra individual del usuario: qué compró, dónde, cuándo, de qué tipo y a cuántos MSI. Cierra la brecha documentada en `05-brechas-compras.md`. Decisión de diseño: **nueva entidad** + **`PurchaseType` como enum en código** (ver ADR-001/ADR-002).

| Campo | Tipo | Notas |
|---|---|---|
| `IdPurchase` | int PK | |
| `IdAccount?` | int FK nullable → `Account` | cascade; cargo en débito |
| `IdCreditCard?` | int FK nullable → `CreditCard` | cascade; cargo a crédito (una de las dos, no ambas) |
| `IdStatement?` | int FK nullable → `Statement` | setnull; line-item del periodo |
| `IdTransaction?` | int FK nullable único → `Transaction` | setnull; reflejo en ledger |
| `Merchant` | string(120) | comercio, ej. `Superama` |
| `Amount` | decimal(18,2) | |
| `Date` | DateOnly | |
| `PurchaseType` | string(20) enum | `fisica` \| `en_linea` \| `recurrente` \| `msi` |
| `InstallmentsTotal?` / `InstallmentNumber?` | int nullable | solo cuando `PurchaseType=msi` |
| `Status` | string(20), default `posted` | `posted`/`pending`/`cancelled` |
| `CreatedAt` | DateTime UTC | |

**Casos de uso**: CU-03c (mis compras + filtro por tipo), CU-06b (line-items del statement), CU-10b (compras de la tarjeta y MSI).
**IA** (propuesto): `GET /me/purchases` → `purchases.list`; `GET …/statements/{id}/purchases` → `statement.purchases`. Placeholders: `{{purchase.merchant}}`, `{{purchase.amount}}`, `{{purchase.type}}`, `{{purchase.installment}}` ("3 de 12 MSI en Liverpool").

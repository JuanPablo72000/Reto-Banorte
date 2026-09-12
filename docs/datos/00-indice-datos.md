# Documentación de datos — Banca Adaptativa

Índice general de la documentación de base de datos, relaciones, casos de uso y consumo por IA.

## Archivos

| # | Archivo | Contenido |
|---|---------|-----------|
| 00 | `00-indice-datos.md` | Este índice, glosario y convenciones (estás aquí) |
| 01 | `01-diagrama-er.md` | Diagrama entidad-relación completo (Mermaid) + por dominios |
| 02 | `02-catalogo-entidades.md` | Ficha de cada entidad: campos, relaciones, reglas, casos de uso, exposición a IA |
| 03 | `03-casos-de-uso.md` | Matriz entidad × caso de uso × endpoint × dataRef × placeholders |
| 04 | `04-evolucion-diseno.md` | Historia en git (`7a56250` → `2cfc9d7`), qué se agregó y por qué |
| 05 | `05-brechas-compras.md` | Brecha: compras del usuario, tipo de compra, line-items de statements. Diseño propuesto `Purchase` |
| 06 | `06-catalogo-ia-placeholders.md` | Catálogo consumible por la IA: dataRefs, acciones, reglas y placeholders |
| 07 | `07-filtros-consultas-ia.md` | Matriz de filtros: parámetros por dataRef para fechas, categorías, cuentas y estados |

Documentos relacionados fuera de `datos/`:

- `../accesibilidad/wcag22-aa.md` — checklist WCAG 2.2 AA por componente + mapeo de preferencias.
- `../arquitectura/adrs/` — Architecture Decision Records (ver `04-evolucion-diseno.md`).
- `../../contracts/a2ui/a2ui-mcp-contract.yaml` — contrato normativo A2UI/MCP (fuente de verdad de dataRefs).

## Glosario

| Término | Significado |
|---------|-------------|
| Entidad / tabla | Clase en `backend/src/BancaAdaptativa.Api/Models/` ↔ tabla EF Core |
| `dataRef` | Referencia simbólica que la IA emite en lugar de datos reales (ej. `transactions.list`). El frontend la resuelve vía API |
| Placeholder | Marcas como `{{account.balance}}` que el frontend sustituye con datos del dataRef correspondiente |
| Statement | Estado de cuenta de un periodo (`Statement` débito / `CreditCardStatement` crédito) |
| ExpenseCategory | Catálogo de categorías de gasto (`gas`, `supermarket`, `transport`, …) |
| Purchase (propuesto) | Compra individual del usuario: comercio, monto, fecha, tipo, MSI. Ver `05-brechas-compras.md` |
| PurchaseType (enum) | `fisica` \| `en_linea` \| `recurrente` \| `msi`. Decisión: enum en código, no tabla |
| MSI | Meses Sin Intereses (`InstallmentsTotal` / `InstallmentNumber` en `Purchase`) |

## Convenciones de la BD (verificadas en `Data/AppDbContext.cs`)

- Todo `DateTime` se guarda normalizado a **UTC** (value converter global) y se lee con `Kind=Utc`.
- `DateOnly` en SQLite se guarda como `TEXT yyyy-MM-dd` (`Transaction.Date`, `DailyBalance.Date`, `Statement.PeriodStart/End`, `StatementExpense.First/LastTransactionDate`, `CreditCardStatement.PaymentDueDate`).
- Montos: `decimal(18,2)`. Moneda por defecto `MXN`. Zona de negocio: `America/Mexico_City` (`Services/BusinessClock.cs`).
- Índices únicos: `User.Email`, `UserProfile.IdUser`, `AccessibilityPreference.IdUser`, `DailyBalance(IdAccount, Date)`, `Transfer.IdempotencyKey`, `ReconciliationMatch.IdTransfer`, `ReconciliationMatch.IdTransaction`, `ExpenseCategory.Code`, `Statement(IdAccount, PeriodStart)`, `StatementExpense(IdStatement, IdExpenseCategory)`, `Budget(IdUser, IdExpenseCategory, Month, Year)`, `CreditCardStatement.IdStatement`.
- `PasswordHash` (BCrypt) **nunca** se expone en DTOs. `MemoryEvent` y `AuditLog` guardan resúmenes **redactados**, nunca datos sensibles crudos.

## Estado actual (resumen)

- **19 entidades / 19 tablas**, 2 migraciones (`InitialCreate`, `StatementsBudgetsGoalsCards`).
- **16 dataRefs** GET + 1 acción (`confirmTransfer`) disponibles para la IA.
- **Brecha conocida**: sin tabla de compras; `CreditCardStatement.TotalPurchases` es solo un agregado mensual.
- **Accesibilidad**: preferencias persistidas + CRUD; sin implementación UI/WCAG todavía.

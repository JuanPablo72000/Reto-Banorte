# ADR-003 — Statements existentes + line-items de compras

- **Estado**: aceptado (diseño; sin implementar en código).
- **Fecha**: 2026-09-12.
- **Contexto**: existen `Statement` (débito, con `StatementExpense` por categoría) y `CreditCardStatement` (1-1 con `Statement` base `AccountType=credito`). Falta el detalle línea por línea. Opciones: documentar tal cual, unificar débito/crédito en un modelo único, o conservar + agregar line-items.

## Opciones consideradas

1. **Conservar + line-items** (elegida): `Purchase.IdStatement?` asignado al generar el statement; `CreditCardStatement.TotalPurchases` pasa a calcularse (`SUM` del periodo) en vez de parámetro manual.
2. **Solo documentar lo existente**: descartada — deja sin resolver CU-06b/CU-10b.
3. **Modelo único de statement**: descartada — el 1-1 actual (`Statement` base + extensión de crédito) ya funciona y lo cubren tests (`PersonalFinanceFlowTests`); unificar sería refactor de alto riesgo sin beneficio.

## Decisión

- `Statement`/`CreditCardStatement`/`StatementExpense` se documentan tal cual (`02-catalogo-entidades.md §2.15–2.16, §2.19`).
- Al generar un statement se asignan sus `Purchase` por rango `[PeriodStart, PeriodEnd]` y origen coincidente.
- `GenerateStatementAsync` calcula `TotalPurchases`; el parámetro actual se marca `Obsolete` una versión.
- Nuevo endpoint `GET …/statements/{id}/purchases` → dataRef `statement.purchases` → componente `StatementPurchases`.

## Consecuencias

- La generación de statements gana una pasada de asignación (idempotente: reasignar solo compras con `IdStatement IS NULL`).
- `StatementExpense` se mantiene para gráficas/presupuestos; los line-items son el detalle navegable.

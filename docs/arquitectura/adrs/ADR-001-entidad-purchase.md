# ADR-001 — Compras como nueva entidad `Purchase`

- **Estado**: aceptado (diseño; sin implementar en código).
- **Fecha**: 2026-09-12.
- **Contexto**: la BD registra movimientos (`Transaction`: monto, fecha, categoría libre) y el agregado mensual `CreditCardStatement.TotalPurchases`, pero no existe qué compró el usuario, dónde, de qué tipo ni a cuántos MSI. Los casos CU-03c, CU-06b y CU-10b lo requieren.

## Opciones consideradas

1. **Nueva entidad `Purchase`** (elegida): tabla con `Merchant`, `Amount`, `Date`, `PurchaseType`, MSI y FKs a cuenta/tarjeta/statement/transaction.
2. **Extender `Transaction`** con columnas comerciales: descartada — contamina el ledger (que debe seguir siendo el registro contable puro) e impide compras `pending/cancelled` sin movimiento.
3. **Ambas (Purchase + link 1-1 a Transaction)**: parcialmente adoptada — `Purchase.IdTransaction?` opcional con `SetNull`, no obligatorio.

## Decisión

Crear `Purchase` según especificación en `docs/datos/05-brechas-compras.md §5.2`: una compra cuelga de `Account` **o** `CreditCard` (check constraint), opcionalmente de `Statement` (line-item, `SetNull`) y de `Transaction` (reflejo 1-1, `SetNull`).

## Consecuencias

- Nueva migración `AddPurchasesAndStatementLineItems`; endpoints `GET /me/purchases`, `…/statements/{id}/purchases`; dataRefs `purchases.list`, `statement.purchases`.
- `Transaction` no cambia: el ledger sigue intacto.

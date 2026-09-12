# ADR-002 — Tipo de compra como enum en código

- **Estado**: aceptado (diseño; sin implementar en código).
- **Fecha**: 2026-09-12.
- **Contexto**: se necesita vocabulario controlado para el tipo de compra (`Purchase.PurchaseType`). El repo ya tiene un patrón de catálogo en tabla (`ExpenseCategory`: `Code` único, FK con `Restrict`).

## Opciones consideradas

1. **Enum en código** (elegida): `fisica | en_linea | recurrente | msi`, validado en el servicio (400 si inválido).
2. **Tabla `PurchaseType`** estilo `ExpenseCategory`: descartada — el conjunto es cerrado y estable; una tabla agregaría migración, seed y CRUD sin beneficio.
3. **String libre + Merchant**: descartada — impide filtrar/agrupar ("mis compras en línea") y rompe la personalización.

## Decisión

`Purchase.PurchaseType string(20)` mapeado a enum en `Models/` (ej. `PurchaseType` enum C# con `Fisica, EnLinea, Recurrente, Msi`). Etiquetas localizadas para UI: "en tienda", "en línea", "recurrente", "a MSI".

## Consecuencias

- Sin migración adicional; si aparecen tipos por marca/tecnología (ej. `contactless`), reevaluar a catálogo.

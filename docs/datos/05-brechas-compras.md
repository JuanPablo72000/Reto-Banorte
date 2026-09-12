# 05 — Brechas: compras del usuario, tipo de compra y line-items de statements

> Estado: **diseño propuesto** (decisiones confirmadas). No existe código; este doc es la especificación para implementarlo.

## 5.1 Qué falta hoy (verificado en código y git)

| Necesidad | Estado actual | Brecha |
|---|---|---|
| Compras del usuario | `Transaction` (monto, fecha, `Category` libre, `Description`) | Sin comercio, sin tipo, sin MSI, sin vínculo a tarjeta |
| Tipo de compra | Solo `Transaction.Category` (string libre: `nomina`, `super`…) | Sin vocabulario controlado |
| Desglose del estado de cuenta | `StatementExpense` agrega por **categoría**; `CreditCardStatement.TotalPurchases` es un **agregado mensual** que se pasa como parámetro manual a `GenerateStatementAsync` | Sin line-items: imposible responder "¿qué compré este periodo?" o "¿cuántos MSI me quedan?" |
| MSI | Inexistente (`grep -i msi/months` → 0 resultados) | Sin parcialidades |

## 5.2 Diseño propuesto: entidad `Purchase`

Decisión ADR-001: **nueva entidad** (no extender `Transaction`), para no contaminar el ledger con atributos comerciales y permitir compras pendientes/canceladas sin movimiento contable.

```csharp
public class Purchase
{
    [Key] public int IdPurchase { get; set; }
    public int? IdAccount { get; set; }        // cargo en débito (una de las dos)
    public int? IdCreditCard { get; set; }     // cargo a crédito
    public int? IdStatement { get; set; }      // line-item del periodo
    public int? IdTransaction { get; set; }    // reflejo en ledger (1-1)

    [MaxLength(120)] public string Merchant { get; set; } = string.Empty;
    [Column(TypeName = "decimal(18,2)")] public decimal Amount { get; set; }
    public DateOnly Date { get; set; }

    [MaxLength(20)] public string PurchaseType { get; set; } = "fisica"; // enum §5.3
    public int? InstallmentsTotal { get; set; }   // solo msi
    public int? InstallmentNumber { get; set; }   // solo msi: parcialidad actual
    [MaxLength(20)] public string Status { get; set; } = "posted"; // posted/pending/cancelled
    public DateTime CreatedAt { get; set; }

    public Account? Account { get; set; }
    public CreditCard? CreditCard { get; set; }
    public Statement? Statement { get; set; }
    public Transaction? Transaction { get; set; }
}
```

Relaciones en `OnModelCreating`:

- `Purchase → Account` N-1, `DeleteBehavior.Cascade`.
- `Purchase → CreditCard` N-1, `Cascade`.
- `Purchase → Statement` N-1 opcional, **`SetNull`** (el line-item sobrevive si se regenera el statement).
- `Purchase → Transaction` 1-1 opcional, `SetNull`, índice único en `IdTransaction`.
- Check constraint: `IdAccount IS NOT NULL OR IdCreditCard IS NOT NULL` (siempre hay origen de fondos) y si `PurchaseType='msi'` entonces `InstallmentsTotal IS NOT NULL`.

Migración propuesta: `AddPurchasesAndStatementLineItems` (crear tabla + FKs + índices `IX_Purchases_IdStatement`, `IX_Purchases_IdCreditCard_Date`).

## 5.3 `PurchaseType`: enum en código (decisión ADR-002)

Valores: `fisica` | `en_linea` | `recurrente` | `msi`. No es tabla (a diferencia de `ExpenseCategory`) porque el conjunto es cerrado y estable; se valida en el servicio con `Enum.TryParse` + 400 si es inválido. Si a futuro aparecen tipos por marca (ej. `contactless`), se reevalúa a catálogo.

## 5.4 Statements con line-items

Regla: al generar un `Statement` (débito o base de crédito), el servicio asigna `Purchase.IdStatement` a las compras cuyo `Date` cae en `[PeriodStart, PeriodEnd]` y cuyo origen (`IdAccount`/`IdCreditCard`) coincide. Efectos:

- `CreditCardStatement.TotalPurchases` **deja de ser parámetro manual** y se calcula como `SUM(Purchase.Amount)` del periodo (cambio en `CreditCardService.GenerateStatementAsync`; mantener el parámetro como `Obsolete` una versión).
- Nuevo endpoint `GET /accounts/{id}/statements/{statementId}/purchases` → dataRef `statement.purchases`.
- `StatementExpense` (agregado por categoría) se mantiene para gráficas; los line-items son el detalle.

## 5.5 Endpoints, DTOs y dataRefs nuevos

| Pieza | Propuesta |
|---|---|
| `GET /me/purchases?type=&from=&to=&cardId=` | lista paginada de compras |
| `GET /me/credit-cards/{id}/purchases` | compras de la tarjeta (incluye MSI activos) |
| `GET /accounts/{id}/statements/{sid}/purchases` | line-items del periodo |
| DTOs | `PurchaseResponse`, `PurchaseListResponse` (con `InstallmentLabel`: "3 de 12") |
| dataRefs | `purchases.list`, `purchase.detail`, `statement.purchases` |
| Componentes | `PurchaseList`, `StatementPurchases` (con `MustBeDataRef:true`, `loading/error/fallback`) |
| Acción | sin acciones de escritura para la IA (las compras las crea el banco, no el usuario) |

## 5.6 Placeholders nuevos

`{{purchase.merchant}}`, `{{purchase.amount}}`, `{{purchase.date}}`, `{{purchase.type}}` (etiqueta localizada: "en línea", "recurrente", "a MSI"), `{{purchase.installment}}` ("3 de 12"), `{{purchases.monthTotal}}`, `{{purchases.onlineTotal}}`, `{{purchases.msiActive}}`.

Ejemplos de redactado (respetando `PlainLanguage`): "Compraste {{purchase.merchant}} por {{purchase.amount}}", "Te quedan {{purchase.remaining}} pagos de {{purchase.installment}} en {{purchase.merchant}}".

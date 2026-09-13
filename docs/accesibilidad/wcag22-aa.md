# Accesibilidad — WCAG 2.2 Nivel AA por componente

> Alcance decidido: checklist por componente. Cubre los 14 componentes A2UI del contrato (`contracts/a2ui/a2ui-mcp-contract.yaml`) + `AccessibilityPanel` + los 2 propuestos (`PurchaseList`, `StatementPurchases`).
> Estado del código (actualizado): frontend implementado — foco visible global, targets ≥ 44px, `aria-live` en respuestas/errores, `prefers-reduced-motion` + `data-reduced-motion`, paletas y plantillas de accesibilidad (`A11yProvider` + panel oculto), tablas con `caption` y gráficas con `accessibility_label`. El checklist de abajo sigue siendo la referencia de aceptación.

## Criterios globales (aplican a todos los componentes)

| Criterio | Nivel | Qué exige | Cómo se cumple |
|---|---|---|---|
| 1.1.1 Contenido no textual | A | iconos e imágenes con alternativa | `CategoryList`: cada icono con `aria-label="{{category.name}}"`; charts con tabla/alternativa textual |
| 1.3.1 Info y relaciones | A | estructura por marcado, no solo visual | listas con `<ul>/<li>`, tablas con `<th scope>`, headings jerárquicos |
| 1.4.1 Uso del color | A | el color no es el único medio | estados (`pending/posted`, progreso) con texto + icono además de color |
| 1.4.3 Contraste mínimo | AA | texto 4.5:1 (3:1 grande) | `HighContrast` garantiza paleta ≥ 7:1; tema base auditado a 4.5:1 |
| 1.4.4 Redimensionar texto | AA | legible al 200% sin pérdida | `FontScale` hasta 2.0 sin scroll horizontal (combina con 1.4.10) |
| 1.4.10 Reflujo | AA | sin scroll bidireccional a 320px | layouts de tarjetas/listas en columna |
| 1.4.11 Contraste no textual | AA | UI y gráficos 3:1 | bordes de foco, barras de progreso, iconos de estado |
| 2.1.1 Teclado | A | todo operable por teclado | filas/cuentas/acciones enfocables y activables con Enter/Espacio |
| 2.4.3 Orden de foco | A | orden lógico | DOM = orden visual en listas y tablas |
| 2.4.7 Foco visible | AA | indicador siempre visible | anillo de foco en todos los interactivos |
| 2.4.11 Foco no oscurecido (mínimo) 🆕2.2 | AA | el foco nunca queda totalmente tapado | sticky headers/modales no cubren el elemento enfocado |
| 2.5.8 Tamaño de objetivo (mínimo) 🆕2.2 | AA | ≥ 24×24 CSS px | `LargeTargets` sube a 44×44; base cumple 24×24 |
| 2.5.7 Movimientos de arrastre 🆕2.2 | AA | alternativa sin arrastrar | charts con tabla de datos y filtros por teclado (sin drag) |
| 3.3.1/3.3.3 Errores | A/AA | identificar + sugerir corrección | `loading/error/fallback` del contrato con mensaje y reintento |
| 4.1.2 Nombre, rol, valor | A | expuesto a AT | roles ARIA correctos (`list`, `table`, `progressbar` con `aria-valuenow`) |
| 4.1.3 Mensajes de estado | AA | `status`/`alert` en vivos | confirmaciones y errores en `aria-live` sin robar foco |

Criterios 2.2 nuevos adicionales a vigilar a nivel página: 3.2.6 Ayuda consistente (A, ayuda en el mismo lugar), 3.3.7 Entrada redundante (A, no re-pedir datos), 3.3.8 Autenticación accesible (AA, login sin pruebas cognitivas — aplica a CU-01).

## Mapeo preferencias → criterios

| Preferencia (`me.preferences`) | Criterios que satisface |
|---|---|
| `FontScale` | 1.4.4, 1.4.10, 1.4.12 (espaciado de texto) |
| `HighContrast` | 1.4.3, 1.4.11 |
| `DarkMode` | 1.4.3, 1.4.11 (paleta alternativa auditada) |
| `ReducedMotion` | 2.3.3 Animación por interacción (AAA, se adopta como AA interno), charts y celebraciones sin movimiento |
| `LargeTargets` | 2.5.8 (44×44 en vez del mínimo 24×24) |
| `PlainLanguage` | 3.1.5 Nivel de lectura (AAA, se adopta como AA interno): redactado simple en IA y UI |

## Checklist por componente

Formato: criterios específicos extra + aceptación testeable. (Los globales de arriba aplican siempre.)

### `StatLabel`, `StatCard` (saldos: `accounts.summary.totalBalance`)
- Extra: 1.3.1 (etiqueta asociada al valor con `<dl>` o `aria-labelledby`).
- Aceptación: lector anuncia "Saldo total, $24,829.25 pesos"; contraste del monto ≥ 4.5:1; escala a 200% sin truncar.

### `AccountList` / `account.detail` (`accounts.list`)
- Extra: 2.4.6 Encabezados y etiquetas (AA): cada cuenta identificada por `Alias` + `MaskedNumber`.
- Aceptación: navegación por teclado entre cuentas; nunca se anuncia número completo; `aria-label="{{account.alias}}, terminada en 1234, saldo {{account.balance}}"`.

### `TransactionList` (`transactions.list`)
- Extra: 1.3.1 (fecha/monto/descripción como celdas o lista estructurada), 3.2.3/3.2.4 (filtros `from/to/category/search` consistentes).
- Aceptación: filtros con `<label>` visible; resultados anuncian conteo vía `aria-live` ("32 movimientos"); dirección crédito/débito con texto, no solo color/signo.

### `DailyBalanceChart` (`dailyBalances.list`)
- Extra: 1.1.1 (alternativa textual: tabla de `{{balance.date}}`/`{{balance.closing}}`), 2.5.7 (sin gestos de arrastre para explorar), `ReducedMotion` desactiva animación.
- Aceptación: el mismo dato existe como tabla accesible; ejes con etiquetas de texto.

### `TransferSummary` + acción `confirmTransfer`
- Extra: 3.3.4 Prevención de errores (AA, datos financieros): resumen revisable + confirmación explícita; 2.4.11 foco visible en el botón de confirmar; 3.3.1 errores (fondos insuficientes identificados por texto).
- Aceptación: flujo completo solo con teclado; confirmación con `requiresConfirmation`; mensaje de éxito en `aria-live`.

### `ReconciliationTable` (`reconciliation.list`)
- Extra: 1.3.1 (`<table>` con `<th scope>`), 1.4.1 (score con texto "coincide/no coincide", no solo color).
- Aceptación: score explicado en lenguaje simple si `PlainLanguage`.

### `StatementList`, `StatementSummary` (`statements.*`, `creditCard.statements`)
- Extra: 2.4.6 (periodo como encabezado: "Estado {{statement.period}}"), 1.1.1 (resumen textual junto a la gráfica).
- Aceptación: `{{statement.topCategory}}` anunciado como texto; tabla de desglose navegable.

### `ExpenseBreakdownChart` (`statements.expenses`)
- Igual que `DailyBalanceChart`: alternativa textual + `ReducedMotion` + segmentos con nombre, no solo color (1.4.1).

### `CategoryList` (`expenseCategories.list`)
- Extra: 1.1.1 (iconos decorativos `aria-hidden` + nombre visible; si el icono es el único contenido, `aria-label`).
- Aceptación: cada categoría es un objetivo ≥ 24px (44px con `LargeTargets`).

### `BudgetProgressCard` (`budgets.monthly`)
- Extra: 4.1.2 (`role="progressbar"` con `aria-valuenow="{{budget.progressPct}}"`), 1.4.1 (exceso de presupuesto con texto "excedido", no solo rojo).
- Aceptación: "Presupuesto {{budget.category}}: {{budget.spent}} de {{budget.limit}}, {{budget.progressPct}}%" anunciado como frase.

### `SavingsGoalCard` (`savingsGoals.list`)
- Igual patrón `progressbar` que `BudgetProgressCard`; celebrar `completed` sin movimiento si `ReducedMotion`; fecha objetivo en formato `es-MX`.

### `CreditCardSummary` (`creditCards.list`)
- Extra: dato sensible — solo `{{card.masked}}`; 2.4.6 (identificación por últimos 4 + `CardType`).
- Aceptación: `{{cardStmt.minimum}}` y `{{cardStmt.dueDate}}` con énfasis textual, no solo visual.

### `AccessibilityPanel` (`me.preferences`)
- Extra: 3.3.2 Etiquetas o instrucciones (A), 1.3.5 Propósito de entrada (AA, `autocomplete` donde aplique), 4.1.3 (confirmar guardado en `aria-live`), 3.2.2 Al cambiar (cada toggle aplica con aviso, sin recargar perdiendo contexto).
- Aceptación: los 6 ajustes operables por teclado, con etiqueta visible y efecto inmediato anunciado.

### `PurchaseList`, `StatementPurchases` 🆕 (`purchases.*`)
- Extra: 2.4.6 (cada compra: "{{purchase.merchant}}, {{purchase.amount}}, {{purchase.date}}"), filtros por `PurchaseType` con `<fieldset>/<legend>`, MSI con texto "3 de 12" (no solo barra).
- Aceptación: agrupación por tipo navegable por headings; sin drag para reordenar.

## Verificación

1. **Automática**: axe-core / Lighthouse en cada página que monte estos componentes (0 violaciones AA).
2. **Manual**: recorrido solo-teclado + lector (NVDA/VoiceOver) por CU (matriz en `../datos/03-casos-de-uso.md`).
3. **Contraste**: muestra de cada paleta (base, `HighContrast`, `DarkMode`) medida ≥ 4.5:1 texto / 3:1 UI.
4. **Contrato IA**: cada render A2UI incluye `skeleton/empty/error` + `a11y.ariaLabel` (ya exigido en `examples/` del YAML).

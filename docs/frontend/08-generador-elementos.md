# Generador de elementos UI del chat

> Cómo pedir un elemento nuevo (a la IA o a un dev) y qué plantillas base
> usar. Todo elemento del chat se escribe en **React + TypeScript +
> Tailwind CSS**, sin dependencias nuevas, siguiendo estas reglas.

## 1. Formato del pedido

Para generar un elemento, entrega:

```yaml
nombre: CreditCardsTable        # PascalCase, sufijo por ui_hint
tool: get_credit_cards          # tool MCP que lo alimenta (TOOL_NAMES)
ui_hint: table                  # table | summary | form | confirmation | none
forma_result:                   # lo que trae step.result (orquestador)
  lista: [{ id_credit_card, card_number_masked, credit_limit, ... }]
muestra: "Tarjeta ****5678, Límite $30,000, Disponible $27,749"
estados: [active]               # status posibles (ver lib/etiquetas.ts)
```

## 2. Convenciones obligatorias (nuestras herramientas)

1. `"use client"` arriba; props `{ step: ExecutedStep }` (de
   `@/lib/types/action-plan`), nada más.
2. Leer datos con `@/lib/plan-result`: `lista<T>()`, `objeto<T>()`,
   `campo()`, `mxn()`, `fecha()`. Jamás `any` suelto ni accesos sin default.
3. Lenguaje humano con `@/lib/etiquetas`: `etiquetaEstado()` +
   `tonoEstado()` + `estadoRelevante()` (columna estado **solo** si alguna
   fila es relevante); `etiquetaCategoria()` para códigos; `esClaveVisible()`
   en fallbacks. Nunca `posted/active/generated` visibles ni `id_*`/`x_*`.
4. Solo primitivas `components/ui` con su vocabulario cerrado:
   `variant: primary|secondary|ghost|danger`, `tone: success|warning|danger|
   info|neutral`, `size: sm|md|lg`. **El tamaño NUNCA se elige a mano**:
   viene de `tamanoEfectivo()` (`lib/layout.ts`) según la plantilla IA
   activa y el override en vivo (ver §5).
5. Vacío → `<EmptyState title description />` (no texto plano).
6. Accesibilidad desde el plan: `aria-label`/`screen_reader_text` en la
   sección, `role="alert"` en errores, `motion-reduce:` en animaciones.
7. Colores solo vía `var(--color-*)` de `globals.css` (paletas
   normal/colorblind/mono). Prohibido hex hardcodeado y clases
   arbitrarias fuera del sistema.
8. `Table` con `caption` + `getRowId` estable; montos con `mxn()`;
   fechas con `fecha()`.
9. Entrada animada: `attrsAnimacion(step.visual.animation, indice)` (si la
   IA no pide animación, entra `fade` con stagger por orden).

## 3. Plantillas base (copiar y adaptar)

### TplTarjetaResumen — `summary` de un objeto
```tsx
"use client";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { campo, mxn, objeto } from "@/lib/plan-result";

export function MiResumen({ step }: { step: ExecutedStep }) {
    const d = objeto<Record<string, unknown>>(step.result);
    if (!d) return null;
    return (
        <Card>
            <p className="text-sm text-[var(--color-text-muted)]">Etiqueta</p>
            <p className="text-3xl font-semibold" aria-live="polite">
                {mxn(campo<number>(d, "total", 0))}
            </p>
            <dl className="mt-3 grid grid-cols-3 gap-2 text-center text-sm max-sm:grid-cols-1 max-sm:text-left">
                {/* pares dt/dd por dato */}
            </dl>
        </Card>
    );
}
```

### TplTabla — `table` de lista (con estado condicional)
```tsx
"use client";
import { Badge } from "@/components/ui/Badge";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { estadoRelevante, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { lista } from "@/lib/plan-result";

interface Fila { id: number; /* ... */ estado: string; }

export function MiTabla({ step }: { step: ExecutedStep }) {
    const rows = lista<Fila>(step.result);
    const mostrarEstado = rows.some((r) => estadoRelevante(r.estado));
    return (
        <Table
            caption="Descripción para lector de pantalla"
            columns={[
                { key: "a", header: "Columna", render: (r) => r.a },
                ...(mostrarEstado
                    ? [{ key: "estado", header: "Estado",
                         render: (r: Fila) => (
                             <Badge tone={tonoEstado(r.estado)}>{etiquetaEstado(r.estado)}</Badge>
                         ) }]
                    : []),
            ]}
            data={rows}
            getRowId={(r) => r.id}
        />
    );
}
```

### TplListaTarjetas — `table`/`summary` de varias tarjetas
Stack de `<Card>` (`flex flex-col gap-2`), badge solo si relevante,
`ProgressBar` para avances. Ver `SavingsGoalsList.tsx`.

### TplDobleVista — tabla + tarjetas conmutables
Envuelve la tabla en `<div className="vista-tabla">` y la versión en
tarjetas en `<div className="vista-cards …">` (el CSS de `globals.css`
muestra una u otra según `data-vista`, que controla el panel de
accesibilidad). Ver `ExpenseCategoriesList.tsx`: lista espaciosa con barra
de participación por defecto + `Table` clásica como alterna.

### TplConfirmación — `confirmation`
`Modal` con resumen + footer Revisar/Confirmar. Lo arma `PlanRenderer`
automático con `pendiente_confirmacion`; no crear uno por tool.

### TplFormulario — `form`
`Input/Select/Button` + errores inline + `aria-describedby`. El submit
real lo dispara el flujo de confirmación del renderer, no el formulario.

### TplGráfica — `visualizations` (no usa `step`)
Las gráficas no salen del `result` del step sino de `plan.visualizations`
(generadas por la IA o por `mcp/app/ia/visualizaciones.py`). En el front
solo se componen con `components/ui/Chart`: `BarChart` (multi-serie
automática: todas las claves numéricas), `LineChart`, `AreaChart`,
`DonutChart` — colores siempre de la paleta activa. `PlanRenderer` ya las
ordena en cuadrícula con `accessibility_label` como fallback de lector.

## 4. Dónde va cada archivo

| Qué | Dónde |
|---|---|
| Elemento de cuentas | `components/accounts/*` |
| De movimientos | `components/transactions/*` |
| De transferencias | `components/transfers/*` |
| De conciliación | `components/reconciliation/*` |
| De balance | `components/balance/*` |
| Registro tool→componente | `REGISTRO` en `components/chat/PlanRenderer.tsx` |
| Icono nuevo | `EXTRAS` en `components/ui/Icon.tsx` (SVG stroke 24px; `PATHS` es del vocabulario del plan) |
| Label/estado nuevo | `lib/etiquetas.ts` |

## 5. Tamaños, posición y ajuste en vivo (no tocar por elemento)

- **Posición**: `lib/layout.ts` coloca cada step por `x_position`
  (`section` + `display_order`) en `PlanLayout`; responsive: `sidebar` →
  stack bajo `lg`, grids 1→2 cols. Ningún elemento decide su lugar.
- **Tamaños**: `size` (`sm/md/lg`) y `font_scale` salen de la plantilla IA
   activa (`tamanoEfectivo()`); el elemento solo consume el `size`.
- **Ajuste en vivo**: panel de accesibilidad (tamaño S/M/L, vista
  tabla↔tarjetas, contraste) guarda el override en `VistaProvider` por
  encima de la plantilla, sin llamar a la IA. No duplicar estos controles
  dentro de elementos.

## 6. Checklist de salida

- [ ] `npx tsc --noEmit` limpio, `npm run lint` 0 errores
- [ ] `EmptyState` en vacío; sin `id_*`/`x_*`/`posted` visibles
- [ ] Responsive: 360px (1 col, stack) y 1024px sin scroll horizontal
- [ ] Lector de pantalla: `caption`/`aria-label`/`aria-live` donde aplique
- [ ] Registrado en `REGISTRO` (o justificado el fallback)

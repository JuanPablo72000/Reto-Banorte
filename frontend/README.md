# Frontend — Banca Personal Adaptativa

App bancaria en **Next.js 16 + Tailwind CSS 4 + recharts**: chat con IA que genera interfaces, menú bancario completo y accesibilidad adaptativa. Sin dependencias de UI externas: todos los primitivos viven en `src/components/ui`.

## Estructura

```
src/
├── app/
│   ├── layout.tsx            # A11yProvider + AuthProvider + globals.css
│   ├── login/page.tsx        # Login híbrido (JWT real o modo demo)
│   ├── (app)/layout.tsx      # Guardia de sesión + VistaProvider + AppShell
│   ├── (app)/page.tsx        # Home: chat 2 paneles (ChatWindow)
│   ├── (app)/accounts|balance|transactions|transfers|statements|cards|budgets|reconciliation|settings/
│   └── api/chat|memory/reset # Puente al MCP (ver abajo)
├── components/
│   ├── layout/AppShell.tsx   # Sidebar, topbar, drawer + tabs móvil, panel a11y
│   ├── chat/                 # ChatWindow, PlanRenderer, ChatComposer, SuggestionBar…
│   ├── accessibility/        # A11yProvider, AccessibilityPanel, toggles
│   ├── accounts|balance|transactions|transfers|reconciliation/  # tarjetas del plan IA
│   ├── ui/                   # Button, Card, Table, Chart, Modal, Badge…
│   └── auth/AuthProvider.tsx # Sesión híbrida en localStorage
├── lib/
│   ├── api/backend.ts        # Cliente REST (.NET) + tipos DTO
│   ├── mcp/client.ts         # Puente stdio a run_turn.py (ejecutarTurno/ejecutarAccion)
│   ├── hooks/useChatPlan.ts  # Lógica del chat reutilizable (enviar/sugerir/confirmar)
│   ├── hooks/useBackendData.ts # Fetch REST con fallback a mocks demo
│   ├── layout.ts + atributos.ts + plantillas.ts  # Posición, animación y plantillas IA
│   └── types/action-plan.ts  # Tipos espejo del ActionPlan del MCP
└── styles/  (tokens en app/globals.css)
```

## Rutas

| Ruta | Qué es |
|---|---|
| `/login` | Entrada. JWT contra `/auth/login`; sin backend entra en **modo demo** (`id_user=1`) |
| `/` | Asistente: panel de chat + panel de interfaces generadas (en móvil, tabs Chat\|Resultados con composer siempre fijo abajo) |
| `/accounts`, `/accounts/[id]` | Cuentas y detalle (REST + bloque "Preguntar a Cain") |
| `/balance`, `/transactions`, `/statements`, `/cards`, `/budgets`, `/reconciliation` | Consultas REST con fallback a mocks + bloques IA |
| `/transfers` | Transferencias por IA (formulario → confirmación → ejecución) + historial |
| `/settings`, `/settings/accessibility` | Perfil, sesión y los mismos controles del panel de accesibilidad |

## Cómo funciona el chat

1. `ChatComposer` envía el texto → `useChatPlan().enviar()` → `POST /api/chat`.
2. `/api/chat` reenvía a `lib/mcp/client.ts`, que lanza `mcp/run_turn.py` por stdio y devuelve el `ActionPlanUI` (incluye el `token` de sesión para que el MCP use la API real).
3. `PlanRenderer` dibuja cada step según su `tool` (`REGISTRO`), el texto según la plantilla activa, `SuggestionBar` (botones con `accion_directa` garantizada), modal de confirmación y la sección de **visualizaciones** en cuadrícula (dona a ancho completo, resto 2 columnas en desktop).
4. Mientras genera, `GenerandoPanel` muestra carga animada con mensajes de progreso; errores van a `ErrorState` con reintento.

## Sistema de diseño (`app/globals.css`)

Todo color sale de variables CSS; **prohibido hex hardcodeado**:

| Selector | Efecto |
|---|---|
| `[data-palette="normal"\|"colorblind"\|"mono"]` | Paleta marca / daltónica / mono-oscura |
| `[data-theme="dark"]` | Tema oscuro |
| `[data-contrast="high"]` | Textos y bordes reforzados |
| `--font-scale` en `<html>` | Todo escala en `rem` (0.85–1.75) |
| `[data-vista="tabla"\|"tarjetas"]` | Tablas ↔ tarjetas sin tocar componentes |
| `[data-density]` + `[data-size]` | Separaciones y targets táctiles (nunca < 44px) |
| `[data-animation]` + `--orden` | Entradas en cascada; `prefers-reduced-motion` y `[data-reduced-motion]` lo apagan todo |

Gráficas (`components/ui/Chart`) usan los colores de la paleta activa, soportan **multi-serie** (p. ej. Gastado/Límite, Usado/Disponible) y tipo `area` además de `bar`/`line`/`pie`/`donut`.

## Accesibilidad

- `A11yProvider`: `theme`, `contrast`, `fontScale`, `reducedMotion`, `palette` → atributos `data-*` + persistencia local.
- `AccessibilityPanel` (oculto por defecto; botón universal o `Alt+A`): letra, paleta, tema, contraste, movimiento, **selector de las 10 plantillas IA** (senior, baja visión, daltonismos…), vista del plan y sección **Memoria y datos guardados** (borrar memoria del asistente vía `POST /api/memory/reset`, restablecer ajustes).
- Plantilla que manda la IA solo pisa preferencias no-default; el override manual del usuario siempre gana.
- Skip link, foco visible global, `aria-live` en respuestas/errores, tooltips y progressbars con nombre accesible.

## Datos: REST con fallback congruente

`lib/api/backend.ts` apunta a `NEXT_PUBLIC_API_URL` (docker: `http://localhost:8000`; dev: `http://localhost:5178`, con CORS ya permitido). `useBackendData` intenta el REST y, si el backend está apagado, usa mocks **congruentes con el seed real y con el mock del MCP**: mismas 4 cuentas y saldos ($164,678.54 MXN), mismo vocabulario de movimientos.

## Comandos

```bash
npm run dev     # desarrollo (http://localhost:3000)
npm run build   # build de producción (verifica TypeScript)
npm run start   # servir el build
npm run lint    # ESLint (0 errores)
```

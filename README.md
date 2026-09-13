# Banca Personal Adaptativa

**Habla con tu banco en lenguaje natural y la interfaz se construye sola, adaptada a ti.**

Escribe *"¿cuánto gasté en restaurantes este mes?"* y obtienes la respuesta en texto claro **más** tablas, tarjetas y gráficas generadas al momento. Si necesitas letra grande, alto contraste o una paleta para daltonismo, la app lo detecta o lo ajustas con dos clics — y lo recuerda.

---

## Lo que puedes hacer

### Asistente con IA (chat)
- Pregunta en español normal: saldos, movimientos, presupuestos, tarjetas, metas de ahorro, estados de cuenta, transferencias.
- Cada respuesta trae **texto + interfaz generada** (tablas, tarjetas, gráficas) que se anima al acomodarse.
- **Gráficas automáticas y ordenadas**: evolución del saldo, gastos por categoría, ingresos vs gastos, presupuesto vs gasto, progreso de metas, crédito usado vs disponible. Puedes pedir rangos de fechas (*"del 1 al 10 de septiembre"*).
- Botones de sugerencia para seguir explorando sin escribir.
- Las operaciones sensibles (transferencias) **siempre piden tu confirmación** antes de ejecutarse.

### Banca completa (menú)
Inicio · Cuentas · Saldos · Movimientos · Transferencias · Estados de cuenta · Tarjetas · Presupuestos y metas · Conciliación · Configuración. Funciona en celular y computadora, con modo demo aunque el servidor esté apagado.

### Accesibilidad real (no un interruptor decorativo)
- Panel oculto (botón universal o `Alt+A`): tamaño de letra, paleta **normal / daltónica / monocromática oscura**, tema claro/oscuro, alto contraste, movimiento reducido.
- **Plantillas IA**: adulto mayor, baja visión, daltonismos, movilidad o cognición reducida, lectura simplificada — la IA las aplica sola cuando detecta la necesidad.
- **Borra la memoria del asistente** cuando quieras, desde el mismo panel.

## Cómo funciona (en 5 pasos)

```
Tú escribes ──▶ IA planea ──▶ Se ejecutan ──▶ Se grafican ──▶ Ves la
"ver mis       qué datos      los datos       los datos       interfaz
 metas"        necesita       reales          ordenados       generada
```

1. **Frontend** (Next.js) recibe tu mensaje y lo envía al puente.
2. **MCP + IA** interpreta la intención, recuerda tus ajustes y arma un plan.
3. El plan consulta el **backend** (.NET + SQLite) o datos demo si no hay servidor.
4. Los números se convierten en **gráficas deterministas** (siempre correctas y ordenadas).
5. El frontend renderiza texto + tablas + gráficas con tu plantilla de accesibilidad.

## Pruébalo en 3 pasos

```powershell
# 1. Levanta todo (construye imágenes, crea la BD demo y verifica salud)
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Reiniciar

# 2. Abre http://localhost:3000
# 3. Entra con:  demo@banorte.mx / Demo123!   (o usa el modo demo)
```

| Servicio | Dónde | Tecnología |
|---|---|---|
| App bancaria | `http://localhost:3000` | Next.js 16 + Tailwind 4 + recharts |
| API de datos | `http://localhost:8000` | .NET 10 Minimal API + SQLite (JWT) |
| Cerebro IA | `http://localhost:8080` | Python + FastMCP + Groq/Gemini |

## Datos demo incluidos

El usuario `demo@banorte.mx` llega con vida financiera completa y coherente: **4 cuentas** ($164,678.54 MXN en total), **~300 movimientos** de 90 días, **3 tarjetas de crédito**, **5 metas de ahorro**, **6 presupuestos** del mes, **10 transferencias** (6 confirmadas, 3 pendientes por confirmar, 1 rechazada), conciliación y estados de cuenta. Todo sirve para simular operaciones reales sin errores.

> Los datos se generan solos al arrancar. Para empezar de cero: `docker compose down -v` (docker) o borra `backend/data/app.db` (local).

## Documentación

- [`frontend/README.md`](frontend/README.md) — guía del frontend: rutas, chat, diseño y accesibilidad.
- [`backend/README.md`](backend/README.md) — guía del backend: endpoints, auth, seed y pruebas.
- [`mcp/README.md`](mcp/README.md) — guía del cerebro IA: tools, orquestador, gráficas y memoria.
- [`docs/frontend/`](docs/frontend/) — puente MCP↔frontend y cómo crear elementos de UI.
- [`docs/datos/`](docs/datos/) — modelo de datos y casos de uso.
- [`docs/accesibilidad/wcag22-aa.md`](docs/accesibilidad/wcag22-aa.md) — checklist WCAG 2.2 AA.

## Notas técnicas

- Local: API en `http://localhost:5178` (`dotnet run`), frontend con `npm run dev`. Requiere **.NET SDK 10**, **Node 22** y claves de IA en `.env` (`GROQ_API_KEY` o `GEMINI_API_KEY`).
- El login real exige `JWT_KEY` configurado (mín. 32 caracteres); sin backend, la app entra en **modo demo** automáticamente.
- Proyecto académico — Reto Banorte.

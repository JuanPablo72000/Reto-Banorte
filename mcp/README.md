# MCP + IA — Cerebro del proyecto

Planificador de IA (Groq + Gemini) y servidor MCP de **Banca Personal Adaptativa**. Recibe un mensaje en lenguaje natural, arma un plan, ejecuta las tools contra la API real (con fallback a mocks) y devuelve el JSON de interfaz que renderiza el frontend — **incluidas las gráficas**.

## Cómo funciona un turno

```
mensaje ──▶ PlannerConMemoria ──▶ orquestador ──▶ JSON de interfaz
            (IA + memoria)        ejecuta steps   (texto + tablas +
                                   (API/mock)     gráficas + sugerencias)
```

- `run_turn.py`: puente de un solo disparo para el frontend (stdin JSON → stdout JSON). Además de turnos acepta la acción `reset_memoria` (borra la memoria del usuario sin llamar a la IA).
- `app/orquestador.py:ejecutar_turno()`: pide el plan, respeta confirmaciones (`prepare/confirm_transfer` quedan `pendiente_confirmacion` sin `confirmado=True`), ejecuta cada step, fuerza `accion_directa` de botones y arma el JSON final con `visualizations`.
- `app/ia/ia_client.py` (`PlannerIA`): genera el `ActionPlan` (intención, steps, sugerencias, plantilla de accesibilidad, visualizaciones libres).
- `app/ia/visualizaciones.py`: **gráficas deterministas desde los resultados reales** (no dependen de la IA): evolución del saldo (área) e ingresos vs gastos (barras) con el rango de fechas en el título, dona de gastos por categoría, barras multi-serie (presupuesto vs gasto, usado vs disponible), progreso de metas, transferencias por mes, créditos vs cargos y conciliación. Ordenadas (tiempo ascendente, categorías descendente), máx. 4 por turno, con `accessibility_label` completo.
- `app/ia/user_memory.py`: memoria por `id_user` (plantilla de accesibilidad + historial, clics, últimos 10 intents, últimos mensajes y notas). Persiste en `.local_memory/user_memory.json`; `reset(id)` la borra.
- `app/tools/tools.py`: **20 tools** (cuentas, movimientos, saldos diarios, transferencias preparar/confirmar, conciliación, statements, categorías de gasto, presupuestos, metas, tarjetas) con fallback automático API → mock.
- `app/placeholders/mock_data.py`: espejo del seed rico del backend — **4 cuentas** ($164,678.54 MXN), 3 tarjetas, 5 metas, 6 presupuestos, 10 transferencias, series de 30 días coherentes (saldo = cierre de la serie).
- `app/server/mcp_server.py`: expone las tools por protocolo MCP (stdio o `MCP_TRANSPORT=http` en `MCP_PORT` 8080).

## Usuario demo (igual que el backend)

`id_user = 1` — `demo@banorte.mx` — perfil con discapacidad visual · `id_account = 1` — "Nómina" ****1234 · transferencia pendiente clásica: $2,000 a "Mamá" (****5678).

## Cómo correr

```bash
cd mcp
python -m venv .venv && .\.venv\Scripts\activate   # Windows (o source .venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env   # pon GROQ_API_KEY (o GEMINI_API_KEY) y BANORTE_API_BASE_URL

python test_local.py                                   # solo el planificador
echo {"mensaje":"ver mis metas","contexto":{},"id_user":1} | python run_turn.py   # turno completo
python -m app.server.mcp_server                        # servidor MCP (stdio)
```

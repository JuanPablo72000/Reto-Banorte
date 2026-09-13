"""
Orquestador de turnos — ejecuta un mensaje completo: plan IA + steps + JSON UI.

Es la versión "producto" del flujo que muestra tests/test_repl_e2e.py:
ese test importa de aquí el cálculo de diff y el dispatcher, y
run_turn.py (puente para el frontend Next.js) expone ejecutar_turno()
como proceso de un solo disparo por stdin/stdout.

Flujo de ejecutar_turno(mensaje, contexto):
  1. PlannerConMemoria.plan -> ActionPlan (con last_raw/last_normalized).
  2. diff raw->final (misma lista de correcciones que ve el test).
  3. Ejecuta cada step contra app.tools (API real con fallback a mock).
     Los steps sensibles (prepare/confirm_transfer) SOLO se ejecutan si
     contexto trae confirmado=True; si no, quedan marcados
     pendiente_confirmacion=True para que el front muestre el modal y
     reenvíe el turno con confirmado=True.
  4. Arma el JSON de interfaz (el bloque [4] del test).

El token JWT del usuario final viaja en contexto["token"]: se exporta
como BANORTE_API_TOKEN para que connection.py lo prefiera sobre el
auto-login demo (ver F5 en docs/frontend/07-puente-mcp-frontend.md).
"""

from __future__ import annotations

import inspect
import logging
import os
from typing import Optional

from app import tools
from app.ia.planner_con_memoria import PlannerConMemoria
from app.ia.visualizaciones import construir_visualizaciones
from app.schemas.schemas import (
    DEFAULT_UI_HINT_BY_TOOL,
    AccessibilityMetadata,
    PlannedStep,
    StepArguments,
    VisualMetadata,
)

logger = logging.getLogger("mcp_ia.orquestador")

_TOOLS_SENSIBLES = ("prepare_transfer", "confirm_transfer")

_TOOLS = {
    nombre: fn
    for nombre, fn in vars(tools).items()
    if inspect.iscoroutinefunction(fn) and not nombre.startswith("_")
}


def calcular_diff(crudo: dict | None, plan) -> list[str]:
    """Compara el JSON crudo del modelo contra el plan final y lista cada
    corrección (normalizador + salvaguarda de memoria) campo por campo."""
    if not isinstance(crudo, dict):
        return ["(sin JSON crudo disponible)"]
    final = plan.model_dump(mode="json")
    cambios: list[str] = []
    for campo in ("intent", "accessibility_template", "needs_confirmation"):
        a, b = crudo.get(campo), final.get(campo)
        if a != b:
            cambios.append(f"{campo}: {a!r} -> {b!r}")
    for i, (s_raw, s_fin) in enumerate(zip(crudo.get("steps", []), final.get("steps", []))):
        tag = (s_raw or {}).get("step_id", f"step_{i}")
        for campo in ("tool", "ui_hint"):
            a, b = (s_raw or {}).get(campo), (s_fin or {}).get(campo)
            if a != b:
                cambios.append(f"{tag}.{campo}: {a!r} -> {b!r}")
        for campo in ("icon", "variant", "tone"):
            a = ((s_raw or {}).get("visual") or {}).get(campo)
            b = ((s_fin or {}).get("visual") or {}).get(campo)
            if a != b:
                cambios.append(f"{tag}.visual.{campo}: {a!r} -> {b!r}")
    for j, (a_raw, a_fin) in enumerate(
        zip(crudo.get("suggested_actions", []), final.get("suggested_actions", []))
    ):
        for campo in ("action_id", "tool", "ui_hint", "icon", "variant", "priority"):
            a, b = (a_raw or {}).get(campo), (a_fin or {}).get(campo)
            if a != b:
                cambios.append(f"sugerencia[{j}].{campo}: {a!r} -> {b!r}")
    return cambios or ["(sin_correcciones)"]


def _resumir(resultado, tope: int = 50):
    if isinstance(resultado, list):
        muestra = resultado[:tope]
        resumido = {
            "total": len(resultado),
            "muestra": [
                r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in muestra
            ],
        }
        if len(resultado) > tope:
            resumido["omitidos"] = len(resultado) - tope
        return resumido
    if hasattr(resultado, "model_dump"):
        return resultado.model_dump(mode="json")
    return resultado


async def _ejecutar_step(tool: str, argumentos: dict):
    fn = _TOOLS.get(tool)
    if fn is None:
        return {"error": f"tool desconocida: {tool!r}", "ejecutado": False}
    aceptados = set(inspect.signature(fn).parameters)
    kwargs = {k: v for k, v in (argumentos or {}).items() if k in aceptados}
    try:
        return {"ejecutado": True, "result": _resumir(await fn(**kwargs))}
    except ValueError as exc:
        return {"error": str(exc), "ejecutado": False}


async def ejecutar_turno(
    mensaje: str,
    contexto: Optional[dict] = None,
    id_user: int = 1,
    planner: Optional[PlannerConMemoria] = None,
) -> dict:
    """Ejecuta un turno completo y regresa el JSON de interfaz (serializable)."""
    contexto = dict(contexto or {})
    contexto.setdefault("id_user", id_user)
    contexto.setdefault("id_account", 1)

    token = contexto.pop("token", None)
    if token:
        os.environ["BANORTE_API_TOKEN"] = str(token)
    confirmado = bool(contexto.get("confirmado", False))

    planner = planner or PlannerConMemoria()
    plan = await planner.plan(id_user=id_user, user_message=mensaje, contexto=contexto)
    crudo = planner.planner.last_raw
    correcciones = calcular_diff(crudo, plan)

    # Botón de sugerencia (SuggestionBar) clickeado: el frontend manda el
    # tool/arguments EXACTOS que ya calculó el turno anterior en
    # contexto["accion_directa"]. Si la IA no lo re-generó igual (o generó
    # un paso vacío/distinto), lo agregamos aquí para que el botón SIEMPRE
    # produzca el resultado prometido, sin depender de que el modelo
    # reinterprete correctamente el texto del botón.
    accion_directa = contexto.get("accion_directa")
    if isinstance(accion_directa, dict) and accion_directa.get("tool"):
        tool_forzada = accion_directa["tool"]
        if not any(s.tool == tool_forzada for s in plan.steps):
            try:
                plan.steps.append(
                    PlannedStep(
                        step_id=f"accion_directa_{tool_forzada}",
                        tool=tool_forzada,
                        ui_hint=DEFAULT_UI_HINT_BY_TOOL.get(tool_forzada, "table"),
                        arguments=StepArguments(**(accion_directa.get("arguments") or {})),
                        reason="Ejecución directa de un botón de sugerencia.",
                        visual=VisualMetadata(),
                        accessibility=AccessibilityMetadata(
                            aria_label=f"Resultado de {tool_forzada}",
                            screen_reader_text=f"Resultado de la acción {tool_forzada}",
                        ),
                        messages={
                            "default": accion_directa.get("label") or "Aquí tienes lo que pediste."
                        },
                    )
                )
            except Exception:
                logger.exception("No se pudo forzar accion_directa=%s", tool_forzada)

    salidas = []
    for step in plan.steps:
        args = step.arguments.model_dump()
        if step.tool in _TOOLS_SENSIBLES and not confirmado:
            logger.info("Step sensible %s sin confirmado=True: queda pendiente", step.tool)
            salidas.append({"ejecutado": False, "pendiente_confirmacion": True})
            continue
        salidas.append(await _ejecutar_step(step.tool, args))

    # Visualizaciones: las de la IA primero (p. ej. bank_card) + las
    # deterministas construidas desde los resultados REALES de los steps
    # (ver app/ia/visualizaciones.py). Dedupe por título; serie temporal
    # ordenada por fecha y categorías por monto dentro de cada gráfica.
    vis_ia = [v for v in (getattr(plan, "visualizations", None) or []) if isinstance(v, dict)]
    pasos_ejecutados = [
        (step.tool, step.arguments.model_dump(), salida)
        for step, salida in zip(plan.steps, salidas)
    ]
    vis_datos = construir_visualizaciones(pasos_ejecutados)
    titulos_ia = {v.get("title") for v in vis_ia}
    visualizaciones = vis_ia + [v for v in vis_datos if v.get("title") not in titulos_ia]

    return {
        "intent": plan.intent,
        "response_to_user": plan.response_to_user,
        "response_to_user_plain_language": plan.response_to_user_plain_language,
        "needs_confirmation": plan.needs_confirmation,
        "accessibility_template": plan.accessibility_template,
        "executed_steps": [
            {
                "step_id": step.step_id,
                "tool": step.tool,
                "ui_hint": step.ui_hint.value,
                "visual": step.visual.model_dump(mode="json"),
                "messages": step.messages,
                **salida,
            }
            for step, salida in zip(plan.steps, salidas)
        ],
        "suggested_actions": [a.model_dump(mode="json") for a in plan.suggested_actions],
        "contextual_tips": plan.contextual_tips,
        "accessibility_recommendations": plan.accessibility_recommendations,
        "visual_theme": plan.visual_theme,
        "visualizations": visualizaciones,
        "depuracion": {
            "modelo": planner.planner.last_model,
            "correcciones": correcciones,
        },
    }

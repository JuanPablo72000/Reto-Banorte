"""
REPL end-to-end — del mensaje al JSON de interfaz, paso a paso.

A diferencia de test_repl_memoria.py (que solo imprime el ActionPlan),
aquí cada mensaje tuyo recorre el pipeline COMPLETO y ves en `print`
los 4 bloques JSON:

  [1] IA crudo ......... lo que devolvió el modelo, sin tocar.
  [2] Normalizado ...... plan tras plan_normalizer (+ salvaguarda de
      memoria) y la lista exacta de correcciones aplicadas.
  [3] Ejecución ........ cada step ejecutado de verdad contra
      BancaAdaptativa.Api (vía app.tools, igual que haría el
      servidor MCP), con su resultado resumido.
  [4] JSON interfaz .... documento final para el front: intent,
      mensajes, executed_steps[] (metadata + result de cada paso),
      sugerencias, tips, plantilla y tema visual.

Si el plan trae prepare_transfer/confirm_transfer, se pausa con
`¿confirmar? (s/n)` antes de ejecutar ese step (n = se salta y se
marca "ejecutado": false).

COMANDOS: /user <id> | /ayuda | /salir (o /exit)

Uso (desde la carpeta mcp/, con el venv activo):
    python tests/test_repl_e2e.py
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()  # DEEPSEEK/GEMINI/BANORTE_* del .env ANTES de importar clientes

from app import tools  # noqa: E402
from app.ia.planner_con_memoria import PlannerConMemoria  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402
from app.schemas import TOOL_NAMES  # noqa: E402

logger = setup_logging(level=logging.INFO)

# Dispatcher: nombre de tool MCP -> corrutina de app.tools (se arma solo
# con las funciones async públicas; sin hardcodear las 20).
_TOOLS = {
    nombre: fn
    for nombre, fn in vars(tools).items()
    if inspect.iscoroutinefunction(fn) and not nombre.startswith("_")
}
_TOOLS_SENSIBLES = ("prepare_transfer", "confirm_transfer")


def _j(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)


def _diff(crudo: dict | None, plan) -> list[str]:
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
        tag = s_raw.get("step_id", f"step_{i}")
        for campo in ("tool", "ui_hint"):
            a, b = s_raw.get(campo), (s_fin or {}).get(campo)
            if a != b:
                cambios.append(f"{tag}.{campo}: {a!r} -> {b!r}")
        for campo in ("icon", "variant", "tone"):
            a = (s_raw.get("visual") or {}).get(campo)
            b = ((s_fin or {}).get("visual") or {}).get(campo)
            if a != b:
                cambios.append(f"{tag}.visual.{campo}: {a!r} -> {b!r}")
    for j, (a_raw, a_fin) in enumerate(
        zip(crudo.get("suggested_actions", []), final.get("suggested_actions", []))
    ):
        for campo in ("action_id", "tool", "ui_hint", "icon", "variant", "priority"):
            a, b = a_raw.get(campo), (a_fin or {}).get(campo)
            if a != b:
                cambios.append(f"sugerencia[{j}].{campo}: {a!r} -> {b!r}")
    return cambios or ["(sin_correcciones)"]


def _resumir(resultado, tope: int = 5):
    """Resume el resultado de una tool para el JSON de interfaz (evita
    volcar tablas gigantes en el print sin perder el total)."""
    if isinstance(resultado, list):
        muestra = resultado[:tope]
        return {
            "total": len(resultado),
            "muestra": [r.model_dump(mode="json") if hasattr(r, "model_dump") else r for r in muestra],
            **({"omitidos": len(resultado) - tope} if len(resultado) > tope else {}),
        }
    if hasattr(resultado, "model_dump"):
        return resultado.model_dump(mode="json")
    return resultado


async def _ejecutar_step(step, argumentos_completos: dict):
    """Invoca la tool del step filtrando los argumentos a los que la
    función acepta (StepArguments trae los 24 campos siempre)."""
    fn = _TOOLS.get(step.tool)
    if fn is None:
        return {"error": f"tool desconocida: {step.tool!r}", "ejecutado": False}
    aceptados = set(inspect.signature(fn).parameters)
    kwargs = {k: v for k, v in argumentos_completos.items() if k in aceptados}
    try:
        resultado = await fn(**kwargs)
    except ValueError as exc:  # contrato: id inexistente, monto inválido...
        return {"error": str(exc), "ejecutado": False}
    return {"ejecutado": True, "result": _resumir(resultado)}


async def main() -> None:
    planner = PlannerConMemoria()
    id_user_activo = 1

    print("=" * 70)
    print("REPL E2E — mensaje -> IA -> corrección -> ejecución -> JSON interfaz")
    print(f"Tools cableadas: {len(_TOOLS)} | usuario: id_user = {id_user_activo}")
    print("Escribe /ayuda para comandos. Flujo por turno: [1] crudo [2] diff [3] exec [4] UI.")
    print("=" * 70)

    while True:
        try:
            linea = input(f"\n[user={id_user_activo}] > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break
        if not linea:
            continue
        if linea in ("/salir", "/exit"):
            print("Hasta luego.")
            break
        if linea == "/ayuda":
            print("/user <id> | /salir")
            continue
        if linea.startswith("/user"):
            partes = linea.split(maxsplit=1)
            if len(partes) != 2 or not partes[1].strip().isdigit():
                print("Uso: /user <id entero>, ej. /user 2")
                continue
            id_user_activo = int(partes[1].strip())
            print(f"Usuario activo ahora: id_user = {id_user_activo}")
            continue

        contexto = {"id_account": 1, "id_user": id_user_activo}
        try:
            plan = await planner.plan(id_user=id_user_activo, user_message=linea, contexto=contexto)
        except Exception as exc:  # noqa: BLE001 — REPL: mostrar y seguir
            print(f"[X] Error llamando al modelo, intenta de nuevo: {exc}")
            continue

        crudo = planner.planner.last_raw
        modelo = planner.planner.last_model

        print(f"\n########## [1] IA crudo (modelo={modelo}) ##########")
        print(_j(crudo))

        print("\n########## [2] Normalizado: correcciones ##########")
        for cambio in _diff(crudo, plan):
            print(f"  ~ {cambio}")

        print("\n########## [3] Ejecución paso a paso ##########")
        args_por_step = []
        for step in plan.steps:
            args = step.arguments.model_dump()
            if step.tool in _TOOLS_SENSIBLES:
                try:
                    r = input(f"  ¿confirmar {step.tool} {json.dumps(args, ensure_ascii=False, default=str)[:120]}? (s/n) > ").strip().lower()
                except (EOFError, KeyboardInterrupt):
                    r = "n"
                if r != "s":
                    print(f"  [{step.step_id}] {step.tool}: OMITIDO por el usuario")
                    args_por_step.append({"error": "omitido por el usuario", "ejecutado": False})
                    continue
            salida = await _ejecutar_step(step, args)
            estado = "OK" if salida.get("ejecutado") else "ERROR"
            print(f"  [{step.step_id}] {step.tool}: {estado}")
            print("  " + _j(salida["result"] if salida.get("ejecutado") else salida).replace("\n", "\n  "))
            args_por_step.append(salida)

        ui_json = {
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
                for step, salida in zip(plan.steps, args_por_step)
            ],
            "suggested_actions": [a.model_dump(mode="json") for a in plan.suggested_actions],
            "contextual_tips": plan.contextual_tips,
            "accessibility_recommendations": plan.accessibility_recommendations,
            "visual_theme": plan.visual_theme,
        }
        print("\n########## [4] JSON para generación de interfaz ##########")
        print(_j(ui_json))


if __name__ == "__main__":
    asyncio.run(main())

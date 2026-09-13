"""
REPL interactivo — PlannerIA + memoria de usuario — NO es parte del
servidor MCP ni del cliente MCP.

A diferencia de test_local.py / test_local_accessibility.py (listas
fijas de casos), aquí escribes TÚ los mensajes en vivo, como si fueras
el usuario, y ves el ActionPlan (JSON) completo de cada turno. Sirve
sobre todo para probar CONTINUIDAD entre turnos: dile en el turno 1 que
eres daltónico, pide algo totalmente distinto en el turno 2 y confirma
que "accessibility_template" sigue siendo el mismo sin que lo repitas.

La memoria persiste en disco (ver DEFAULT_MEMORY_PATH en
app/ia/user_memory.py: mcp/.local_memory/user_memory.json), así que si
cierras y vuelves a abrir el REPL, el mismo id_user sigue recordando lo
de antes. Usa /reset si quieres empezar de cero.

COMANDOS (además de escribir un mensaje normal):
  /user <id>            cambia el id_user activo (default: 1)
  /click <funcion> [n]  registra n clics (default 1) en esa función,
                         SIN llamar al modelo -- para simular lo que
                         mandaría el frontend antes del próximo mensaje
  /memoria              muestra el perfil de memoria del usuario activo
                          (sin llamar a la IA)
  /reset                borra la memoria del usuario activo
  /ayuda                vuelve a mostrar esta lista de comandos
  /salir  (o /exit)     termina el REPL

Cualquier otra línea se manda tal cual como mensaje del usuario al
ActionPlan, con id_account=1 fijo (ver seed real en
backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs).

Uso (desde la carpeta mcp/, con el venv activo):
    python test_repl_memoria.py
"""

import asyncio
import json
import logging

from dotenv import load_dotenv

load_dotenv()  # carga DEEPSEEK_API_KEY del .env ANTES de importar ia_client

from app.ia.planner_con_memoria import PlannerConMemoria
from app.logging_config import setup_logging

logger = setup_logging(level=logging.INFO)

AYUDA = __doc__.split("COMANDOS")[1].split("Cualquier otra línea")[0]


def _parsear_click(linea: str) -> tuple[str, int] | None:
    """Parsea '/click funcion 3' o '/click funcion' (cantidad=1)."""
    partes = linea.split(maxsplit=2)[1:]  # quita "/click"
    if not partes:
        return None
    funcion = partes[0]
    cantidad = 1
    if len(partes) > 1:
        try:
            cantidad = int(partes[1])
        except ValueError:
            print(f"⚠️  '{partes[1]}' no es un número, se usa cantidad=1")
    return funcion, cantidad


async def main() -> None:
    planner = PlannerConMemoria()
    id_user_activo = 1

    print("=" * 60)
    print("REPL — PlannerIA con memoria de usuario")
    print("Usuario activo: id_user =", id_user_activo)
    print("Escribe /ayuda para ver los comandos disponibles.")
    print("=" * 60)

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
            print(AYUDA)
            continue

        if linea.startswith("/user"):
            partes = linea.split(maxsplit=1)
            if len(partes) != 2 or not partes[1].strip().isdigit():
                print("Uso: /user <id entero>, ej. /user 2")
                continue
            id_user_activo = int(partes[1].strip())
            print(f"Usuario activo ahora: id_user = {id_user_activo}")
            continue

        if linea.startswith("/click"):
            resultado = _parsear_click(linea)
            if resultado is None:
                print("Uso: /click <funcion> [cantidad], ej. /click prepare_transfer 3")
                continue
            funcion, cantidad = resultado
            perfil = await planner.memoria.registrar_clicks(id_user_activo, {funcion: cantidad})
            print(f"✅ Clic(s) registrado(s): {funcion} +{cantidad} (total ahora: {perfil.clics[funcion]})")
            continue

        if linea == "/memoria":
            perfil = await planner.memoria.obtener_perfil(id_user_activo)
            print(json.dumps(perfil.to_dict(), indent=2, ensure_ascii=False))
            continue

        if linea == "/reset":
            await planner.memoria.reset(id_user_activo)
            print(f"🗑️  Memoria de id_user={id_user_activo} borrada.")
            continue

        # Cualquier otra cosa: mensaje normal al ActionPlan.
        contexto = {"id_account": 1, "id_user": id_user_activo}
        try:
            plan = await planner.plan(id_user=id_user_activo, user_message=linea, contexto=contexto)
        except Exception as exc:  # noqa: BLE001 — REPL: mostrar y seguir, nunca morir
            print(f"⚠️  Error llamando al modelo, intenta de nuevo: {exc}")
            continue

        print(json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False))
        print(f"\n>>> accessibility_template: {plan.accessibility_template} | intent: {plan.intent}")


if __name__ == "__main__":
    asyncio.run(main())

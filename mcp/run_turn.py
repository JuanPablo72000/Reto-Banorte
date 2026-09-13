"""
Puente de un solo disparo para el frontend Next.js (ver
frontend/src/lib/mcp/client.ts y docs/frontend/07-puente-mcp-frontend.md).

Lee UN JSON por stdin: {"mensaje": str, "contexto": {...}, "id_user": int}
Ejecuta app.orquestador.ejecutar_turno e imprime el JSON de interfaz por
stdout. Los logs van a stderr (nunca stdout: ahí solo va el JSON).

Uso:
    echo {"mensaje": "ver mi saldo", "contexto": {}} | python run_turn.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()  # DEEPSEEK/GEMINI/BANORTE_* del .env ANTES de importar clientes

from app.logging_config import setup_logging  # noqa: E402
from app.orquestador import ejecutar_turno  # noqa: E402

setup_logging(level=logging.INFO)
logger = logging.getLogger("mcp_ia.run_turn")


async def main() -> int:
    try:
        pedido = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"stdin no es JSON válido: {exc}"}), flush=True)
        return 2

    id_user = int(pedido.get("id_user", 1))

    # Acciones de mantenimiento que NO llaman a la IA (baratas, sin token
    # de Groq). Hoy: borrar la memoria del usuario desde el panel de
    # accesibilidad del frontend.
    accion = str(pedido.get("accion") or "").strip()
    if accion == "reset_memoria":
        from app.ia.user_memory import DEFAULT_MEMORY_PATH, MemoriaUsuarioStore

        store = MemoriaUsuarioStore(DEFAULT_MEMORY_PATH)
        await store.reset(id_user)
        print(json.dumps({"ok": True, "memoria_borrada": True, "id_user": id_user}), flush=True)
        return 0
    if accion:
        print(json.dumps({"error": f"accion desconocida: {accion!r}"}), flush=True)
        return 2

    mensaje = (pedido.get("mensaje") or "").strip()
    if not mensaje:
        print(json.dumps({"error": "falta 'mensaje' en el pedido"}), flush=True)
        return 2
    try:
        ui_json = await ejecutar_turno(
            mensaje,
            contexto=pedido.get("contexto") or {},
            id_user=id_user,
        )
    except Exception as exc:  # noqa: BLE001 — el puente nunca muere sin JSON
        logger.exception("Turno fallido")
        print(json.dumps({"error": f"turno fallido: {exc}"}), flush=True)
        return 1
    print(json.dumps(ui_json, ensure_ascii=False, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

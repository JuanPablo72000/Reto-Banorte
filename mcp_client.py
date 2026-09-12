"""
Cliente MCP — parte de Guillermo (MCP + modelo de IA).

Este script:
1. Levanta app/server/mcp_server.py como subproceso (transporte stdio,
   igual que lo haría Cain al integrar, o un futuro host de IA tipo
   Claude Desktop).
2. Lista las tools que el servidor expone (para verificar que las 8 tools
   de datos + planificar_accion están bien registradas).
3. Llama a un par de tools de datos directamente (get_user_context,
   get_accounts) usando el usuario/cuenta semilla real (id=1, ver
   backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs) para probar el flujo
   MCP de punta a punta.
4. Llama a `planificar_accion` con un mensaje de usuario y muestra el
   ActionPlan resultante ya como JSON tipado — el mismo JSON que Cain
   consumirá y que el front recorrerá para generar la interfaz.

Uso (desde la carpeta mcp/, con el venv activo):
    python mcp_client.py
    python mcp_client.py "Quiero ver mis movimientos del mes pasado"
"""

import asyncio
import json
import logging
import sys

from fastmcp import Client

from app.logging_config import setup_logging

logger = setup_logging(level=logging.INFO)

SERVER_SCRIPT = "app/server/mcp_server.py"

# IDs semilla reales (DbSeeder.cs): usuario demo id=1, su cuenta "Nómina" id=1.
ID_USER_DEMO = 1
ID_ACCOUNT_DEMO = 1


def _print_header(titulo: str) -> None:
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")


async def main() -> None:
    mensaje_usuario = (
        sys.argv[1] if len(sys.argv) > 1 else "Quiero ver mis movimientos del mes pasado"
    )

    # Client(SERVER_SCRIPT) arranca el servidor como subproceso stdio y
    # habla el protocolo MCP real (initialize, tools/list, tools/call...).
    client = Client(SERVER_SCRIPT)

    async with client:
        # 1. Descubrir tools disponibles (esto es lo que vería cualquier
        #    host MCP real, incluyendo un futuro traductor a UI: cada tool
        #    trae su JSON Schema de entrada/salida ya generado por FastMCP).
        _print_header("TOOLS DISPONIBLES EN EL SERVIDOR")
        tools = await client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description.strip().splitlines()[0] if tool.description else ''}")

        # 2. Probar una tool de datos simple (get_user_context)
        _print_header(f"get_user_context(id_user={ID_USER_DEMO})")
        result = await client.call_tool("get_user_context", {"id_user": ID_USER_DEMO})
        print(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))

        # 3. Probar otra tool de datos (get_accounts)
        _print_header(f"get_accounts(id_user={ID_USER_DEMO})")
        result = await client.call_tool("get_accounts", {"id_user": ID_USER_DEMO})
        print(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))

        # 4. Probar la orquestación con IA de punta a punta vía protocolo MCP
        _print_header(f"planificar_accion(mensaje_usuario={mensaje_usuario!r})")
        result = await client.call_tool(
            "planificar_accion",
            {
                "mensaje_usuario": mensaje_usuario,
                "contexto": {"id_user": ID_USER_DEMO, "id_account": ID_ACCOUNT_DEMO},
            },
        )
        print(json.dumps(result.data, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    asyncio.run(main())

"""
Script de prueba local — NO es parte del servidor MCP ni del cliente MCP.

Sirve para probar PlannerIA directamente, sin necesitar un cliente MCP
real (para eso está mcp_client.py). Así puedes ver rápido si tu API key
funciona y qué ActionPlan tipado devuelve el modelo para distintos mensajes
de usuario, usando los IDs enteros reales del seed (id_user=1, id_account=1
— ver backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs).

Uso (desde la carpeta mcp/, con el venv activo):
    python test_local.py
"""

import asyncio
import json
import logging

from dotenv import load_dotenv

load_dotenv()  # carga DEEPSEEK_API_KEY del .env ANTES de importar ia_client

from app.ia.ia_client import PlannerIA
from app.logging_config import setup_logging

logger = setup_logging(level=logging.INFO)


async def main() -> None:
    planner = PlannerIA()

    casos_de_prueba = [
        {
            "mensaje": "Quiero ver mis movimientos del mes pasado",
            "contexto": {"id_account": 1, "id_user": 1},
        },
        {
            "mensaje": "Transfiere 500 pesos a mi hermano",
            "contexto": {"id_account": 1, "id_user": 1},
        },
        {
            "mensaje": "Hola, ¿qué puedes hacer?",
            "contexto": {},
        },
    ]

    for i, caso in enumerate(casos_de_prueba, start=1):
        print(f"\n{'=' * 60}")
        print(f"CASO {i}: {caso['mensaje']}")
        print("=" * 60)

        plan = await planner.plan(user_message=caso["mensaje"], context=caso["contexto"])

        # ActionPlan ya es un modelo Pydantic tipado (schemas.py): esto es
        # exactamente el JSON que consumirá Cain y, más adelante, el
        # traductor a interfaz visual.
        print(json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())

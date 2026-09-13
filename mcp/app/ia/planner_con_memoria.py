"""
PlannerIA + memoria de usuario — parte de Guillermo (MCP + modelo de IA).

Combina PlannerIA (sin estado, ver ia_client.py) con
MemoriaUsuarioStore (ver user_memory.py) para que:

  1. Los clics que reporta el frontend se acumulen por usuario.
  2. La plantilla de accesibilidad detectada en un turno se recuerde en
     los siguientes, aunque el usuario no repita la condición.
  3. El modelo reciba ese estado como parte de "context" bajo la llave
     "memoria_usuario" (ver la regla 14 de SYSTEM_INSTRUCTION en
      ia_client.py, que le dice explícitamente cómo usarlo).
  4. Aunque el modelo IGNORE esa instrucción (pasa con modelos chicos
     como gpt-oss-20b bajo carga): si devuelve "default" pero el usuario
     ya tenía otra plantilla guardada y el mensaje actual no pide
     explícitamente quitarla, se conserva la anterior en código (ver
     _es_reset_explicito) -- no dependemos solo del prompt.

Este es el punto de entrada que debería usar el servidor MCP
(mcp_server.py) en vez de instanciar PlannerIA directo, para que la
continuidad entre turnos no dependa de que cada caller se acuerde de
armar a mano el contexto de memoria.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.ia.ia_client import PlannerIA
from app.ia.user_memory import DEFAULT_MEMORY_PATH, MemoriaUsuarioStore
from app.schemas import ActionPlan

logger = logging.getLogger("mcp_ia.planner_con_memoria")

# Si el mensaje actual contiene alguna de estas pistas, SÍ dejamos que el
# accessibility_template baje a "default" aunque el usuario tuviera algo
# guardado -- es una señal de que quiere quitar/desactivar el ajuste a
# propósito, no que el modelo simplemente lo haya olvidado.
_PALABRAS_RESET_ACCESIBILIDAD = (
    "ya no", "quita el", "quítale", "quítalo", "sin accesibilidad",
    "vuelve a lo normal", "restablece", "reset", "modo normal",
    "modo default", "por defecto", "desactiva", "ya se me quitó",
    "ya no tengo problema", "ya no necesito",
)


def _es_reset_explicito(mensaje: str) -> bool:
    texto = (mensaje or "").lower()
    return any(palabra in texto for palabra in _PALABRAS_RESET_ACCESIBILIDAD)


class PlannerConMemoria:
    """Ver docstring del módulo. Un objeto de esta clase se puede reusar
    entre requests (guarda el mismo MemoriaUsuarioStore, que a su vez
    persiste a disco en cada escritura)."""

    def __init__(
        self,
        planner: Optional[PlannerIA] = None,
        memoria: Optional[MemoriaUsuarioStore] = None,
        ruta_memoria: Optional[str] = DEFAULT_MEMORY_PATH,
    ) -> None:
        self.planner = planner or PlannerIA()
        self.memoria = memoria or MemoriaUsuarioStore(ruta_memoria)

    async def plan(
        self,
        id_user: int,
        user_message: str,
        contexto: Optional[dict] = None,
        clicks: Optional[dict[str, int]] = None,
    ) -> ActionPlan:
        """Genera un ActionPlan enriquecido CON continuidad entre turnos.

        id_user: de quién es la memoria a leer/actualizar.
        contexto: lo mismo que ya le mandabas a PlannerIA.plan()
            (id_account, id_user, etc. — ver test_local.py).
        clicks: lo que el FRONTEND reporta en ESTE request, ej.
            {"prepare_transfer": 1, "get_transactions": 3}. Se suma al
            contador acumulado de ese usuario ANTES de llamar al modelo,
            así que ya puede influir en las sugerencias de esta misma
            respuesta (ver regla 14). Opcional: si no hay clics nuevos
            en este turno, no mandes nada o manda {}.
        """
        contexto_final = dict(contexto or {})

        if clicks:
            await self.memoria.registrar_clicks(id_user, clicks)

        perfil_previo = await self.memoria.obtener_perfil(id_user)
        contexto_memoria = await self.memoria.contexto_para_prompt(id_user)
        contexto_final.update(contexto_memoria)

        plan = await self.planner.plan(user_message=user_message, context=contexto_final)

        # Salvaguarda además de la regla 14 del prompt: no confiamos SOLO
        # en que el modelo obedezca la instrucción de mantener la
        # accesibilidad. Si el modelo devolvió "default" pero el usuario
        # ya tenía algo distinto guardado, y el mensaje actual no pide
        # explícitamente quitarlo/cambiarlo, se conserva lo anterior. Esto
        # evita que un olvido del modelo (modelos chicos como
        # gpt-oss-20b no siempre siguen instrucciones largas al pie de la
        # letra) le borre la accesibilidad al usuario de la nada.
        if (
            plan.accessibility_template == "default"
            and perfil_previo.accessibility_template_actual != "default"
            and not _es_reset_explicito(user_message)
        ):
            logger.info(
                "Modelo devolvió accessibility_template='default' pero id_user=%s ya tenía %r "
                "guardado y el mensaje no pide quitarlo explícitamente; se conserva %r por continuidad.",
                id_user, perfil_previo.accessibility_template_actual, perfil_previo.accessibility_template_actual,
            )
            plan.accessibility_template = perfil_previo.accessibility_template_actual

        # Persistir lo que ESTE turno decidió (ya con la salvaguarda
        # aplicada), para que el SIGUIENTE turno lo herede sin que el
        # usuario tenga que repetirlo.
        await self.memoria.actualizar_accesibilidad(
            id_user, plan.accessibility_template, motivo=user_message
        )
        await self.memoria.registrar_intent(id_user, plan.intent)

        return plan

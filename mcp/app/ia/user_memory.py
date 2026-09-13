"""
Memoria de usuario — accesibilidad detectada + contador de clics por
función — parte de Guillermo (MCP + modelo de IA).

POR QUÉ EXISTE:
  PlannerIA (ia_client.py) es completamente SIN ESTADO: cada llamada
  a `plan()` solo ve el mensaje actual y el "context" que le pasemos,
  nada de lo que pasó antes. Si en el turno 1 alguien dice "soy
  daltónico" y en el turno 2 solo dice "transfiere 500 pesos", sin
  memoria el modelo no tiene forma de saber que sigue siendo daltónico
  -> vuelve a "default" y el usuario pierde su ajuste de accesibilidad
  cada vez que cambia de tema.

  Este módulo guarda, por id_user:
    - accessibility_template_actual: la última plantilla de
      accesibilidad confirmada/inferida (ver
      app/ia/accessibility_templates.py), con un historial corto de
      cambios (para poder ver CUÁNDO y POR QUÉ cambió).
    - clics: cuántas veces el FRONTEND reportó que el usuario tocó cada
      función/botón. El conteo real vive en el frontend; aquí solo se
      acumula lo que nos manda, nunca lo inventamos.
    - intents_recientes: los últimos intents del ActionPlan, para dar
      un poco de continuidad conversacional sin mandarle a la IA el
      historial completo de mensajes (eso infla mucho el prompt — ya
      hemos visto 413 "tokens per minute" solo con el schema base).

  QUÉ NO ES esto: no es la base de datos real de Preferences ni de
  MemoryEvent (ver schemas.py) — esas viven en BancaAdaptativa.Api y hoy
  NO tienen endpoint expuesto para IA (comentario ya existente en
  schemas.py sobre search_memory_context). Este módulo es el stand-in
  local/de demo mientras ese endpoint no exista: el día que exista,
  `MemoriaUsuarioStore` debería volverse un cliente de ese endpoint en
  vez de leer/escribir un archivo JSON local — la interfaz pública
  (obtener_perfil/registrar_clicks/actualizar_accesibilidad/...) no
  tendría que cambiar para quien la usa.

PERSISTENCIA: por default guarda en un archivo JSON local (ver
DEFAULT_MEMORY_PATH) para que sobreviva a reinicios del proceso durante
pruebas locales (ver test_repl_memoria.py). Pasa `ruta_archivo=None`
para usar memoria puramente en RAM (útil en tests unitarios que no
deben tocar disco).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATE_IDS

logger = logging.getLogger("mcp_ia.user_memory")

# mcp/.local_memory/user_memory.json (relativo a este archivo:
# app/ia/user_memory.py -> app/ia -> app -> mcp)
DEFAULT_MEMORY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    ".local_memory",
    "user_memory.json",
)

# Cuántos intents/cambios de accesibilidad se guardan como máximo por
# usuario. Es memoria de continuidad de CORTO plazo, no un log completo
# (para eso están AuditLog/MemoryEvent del backend real — ver schemas.py).
MAX_INTENTS_RECIENTES = 10
MAX_HISTORIAL_ACCESIBILIDAD = 8
MAX_MENSAJES_RECIENTES = 6
MAX_NOTAS = 8
MAX_LARGO_MENSAJE = 140


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class PerfilMemoriaUsuario:
    """Todo lo que recordamos de un id_user entre turnos/sesiones."""

    id_user: int
    accessibility_template_actual: str = "default"
    accessibility_historial: list[dict] = field(default_factory=list)
    clics: dict[str, int] = field(default_factory=dict)
    intents_recientes: list[str] = field(default_factory=list)
    # Últimos mensajes del usuario con su intent y fecha (continuidad rica:
    # la IA puede referirse a lo que el usuario pidió hace un par de turnos).
    ultimos_mensajes: list[dict] = field(default_factory=list)
    # Notas libres clave->valor (destinos frecuentes de transferencia,
    # preferencias declaradas, etc.). Las escribe el orquestador/IA.
    notas: dict[str, str] = field(default_factory=dict)
    actualizado_en: str = field(default_factory=_ahora_iso)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PerfilMemoriaUsuario":
        return cls(
            id_user=data["id_user"],
            accessibility_template_actual=data.get("accessibility_template_actual", "default"),
            accessibility_historial=data.get("accessibility_historial", []),
            clics=data.get("clics", {}),
            intents_recientes=data.get("intents_recientes", []),
            ultimos_mensajes=data.get("ultimos_mensajes", []),
            notas=data.get("notas", {}),
            actualizado_en=data.get("actualizado_en", _ahora_iso()),
        )


class MemoriaUsuarioStore:
    """Guarda y recupera el PerfilMemoriaUsuario de cada id_user.

    Es async-safe (un asyncio.Lock por instancia): el servidor MCP puede
    atender varias sesiones/usuarios "al mismo tiempo" (varias tareas
    async), y todas comparten el mismo archivo en disco.
    """

    def __init__(self, ruta_archivo: Optional[str] = DEFAULT_MEMORY_PATH):
        self._ruta_archivo = ruta_archivo
        self._lock = asyncio.Lock()
        self._perfiles: dict[int, PerfilMemoriaUsuario] = {}
        self._cargar_desde_disco()

    # -- persistencia ---------------------------------------------------
    def _cargar_desde_disco(self) -> None:
        if not self._ruta_archivo or not os.path.exists(self._ruta_archivo):
            return
        try:
            with open(self._ruta_archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            for id_user_str, perfil_data in datos.items():
                perfil = PerfilMemoriaUsuario.from_dict(perfil_data)
                self._perfiles[int(id_user_str)] = perfil
            logger.info(
                "Memoria de usuario cargada desde %s (%d perfiles)",
                self._ruta_archivo, len(self._perfiles),
            )
        except (json.JSONDecodeError, OSError, KeyError, ValueError) as exc:
            logger.warning(
                "No se pudo cargar memoria de usuario desde %s (%s). Se empieza vacío.",
                self._ruta_archivo, exc,
            )

    def _guardar_en_disco(self) -> None:
        if not self._ruta_archivo:
            return
        os.makedirs(os.path.dirname(self._ruta_archivo), exist_ok=True)
        datos = {str(id_user): perfil.to_dict() for id_user, perfil in self._perfiles.items()}
        ruta_temp = f"{self._ruta_archivo}.tmp"
        # Escritura atómica (escribe a un temp y renombra) para no dejar
        # el JSON a medias si el proceso muere justo al guardar.
        with open(ruta_temp, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        os.replace(ruta_temp, self._ruta_archivo)

    # -- lectura ----------------------------------------------------------
    def _obtener_o_crear(self, id_user: int) -> PerfilMemoriaUsuario:
        if id_user not in self._perfiles:
            self._perfiles[id_user] = PerfilMemoriaUsuario(id_user=id_user)
        return self._perfiles[id_user]

    async def obtener_perfil(self, id_user: int) -> PerfilMemoriaUsuario:
        async with self._lock:
            return self._obtener_o_crear(id_user)

    async def contexto_para_prompt(self, id_user: int, top_n_clics: int = 5) -> dict:
        """Dict listo para mezclarse en el "context" que se le pasa a
        PlannerIA.plan() (ver regla 14 del SYSTEM_INSTRUCTION en
        ia_client.py). Se manda TAL CUAL dentro del JSON del prompt,
        así que se mantiene chico a propósito: solo el top N de clics,
        los últimos N intents, 3 mensajes recientes y hasta 5 notas."""
        async with self._lock:
            perfil = self._obtener_o_crear(id_user)
            clics_top = dict(
                sorted(perfil.clics.items(), key=lambda kv: kv[1], reverse=True)[:top_n_clics]
            )
            mensajes = [
                {"mensaje": m.get("mensaje", ""), "intent": m.get("intent", "")}
                for m in perfil.ultimos_mensajes[-3:]
            ]
            notas = dict(list(perfil.notas.items())[:5])
            return {
                "memoria_usuario": {
                    "accessibility_template_previo": perfil.accessibility_template_actual,
                    "clics_frecuentes": clics_top,
                    "intents_recientes": perfil.intents_recientes[-MAX_INTENTS_RECIENTES:],
                    "mensajes_recientes": mensajes,
                    "notas": notas,
                }
            }

    # -- escritura ----------------------------------------------------------
    async def registrar_clicks(self, id_user: int, clicks: dict[str, int]) -> PerfilMemoriaUsuario:
        """Suma los clics que reporta el frontend para este id_user.

        `clicks` es lo que manda el frontend en ESTE request, ej.
        {"prepare_transfer": 1, "get_transactions": 3}. Se recomienda
        usar los mismos nombres de TOOL_NAMES/CANONICAL_ACTION_IDS
        (schemas.py) para que "clics_frecuentes" sea consistente con el
        resto del sistema, pero no es obligatorio: cualquier string sirve
        como llave."""
        async with self._lock:
            perfil = self._obtener_o_crear(id_user)
            for funcion, cantidad in clicks.items():
                if cantidad <= 0:
                    continue
                perfil.clics[funcion] = perfil.clics.get(funcion, 0) + int(cantidad)
            perfil.actualizado_en = _ahora_iso()
            self._guardar_en_disco()
            return perfil

    async def actualizar_accesibilidad(
        self, id_user: int, template_id: str, motivo: str = ""
    ) -> PerfilMemoriaUsuario:
        """Guarda la plantilla de accesibilidad que el ActionPlan más
        reciente decidió, para que el PRÓXIMO turno la recuerde aunque
        ese turno no vuelva a mencionar la condición.

        Si template_id no está en el catálogo fijo
        (ACCESSIBILITY_TEMPLATE_IDS) se ignora — nunca guardamos un id
        inventado por el modelo."""
        if template_id not in ACCESSIBILITY_TEMPLATE_IDS:
            logger.warning(
                "accessibility_template %r fuera de catálogo, no se guarda en memoria",
                template_id,
            )
            return await self.obtener_perfil(id_user)

        async with self._lock:
            perfil = self._obtener_o_crear(id_user)
            if template_id != perfil.accessibility_template_actual:
                perfil.accessibility_historial.append({
                    "template": template_id,
                    "template_anterior": perfil.accessibility_template_actual,
                    "motivo": (motivo or "")[:200],
                    "actualizado_en": _ahora_iso(),
                })
                perfil.accessibility_historial = perfil.accessibility_historial[-MAX_HISTORIAL_ACCESIBILIDAD:]
                perfil.accessibility_template_actual = template_id
                perfil.actualizado_en = _ahora_iso()
                self._guardar_en_disco()
            return perfil

    async def registrar_intent(self, id_user: int, intent: str, mensaje: str = "") -> PerfilMemoriaUsuario:
        """Registra el intent del turno y, si se pasa, un extracto del
        mensaje del usuario (recortado a MAX_LARGO_MENSAJE) para dar
        continuidad conversacional más rica entre turnos."""
        async with self._lock:
            perfil = self._obtener_o_crear(id_user)
            perfil.intents_recientes.append(intent)
            perfil.intents_recientes = perfil.intents_recientes[-MAX_INTENTS_RECIENTES:]
            texto = (mensaje or "").strip()[:MAX_LARGO_MENSAJE]
            if texto:
                perfil.ultimos_mensajes.append({
                    "mensaje": texto,
                    "intent": intent,
                    "en": _ahora_iso(),
                })
                perfil.ultimos_mensajes = perfil.ultimos_mensajes[-MAX_MENSAJES_RECIENTES:]
            perfil.actualizado_en = _ahora_iso()
            self._guardar_en_disco()
            return perfil

    async def registrar_nota(self, id_user: int, clave: str, valor: str) -> PerfilMemoriaUsuario:
        """Guarda una nota libre clave->valor (ej. "destino_frecuente":
        "Mamá ****5678"). Sobrescribe la clave si ya existía; recorta a
        MAX_NOTAS entradas (FIFO por inserción)."""
        async with self._lock:
            perfil = self._obtener_o_crear(id_user)
            perfil.notas[clave.strip()[:60]] = (valor or "").strip()[:200]
            if len(perfil.notas) > MAX_NOTAS:
                perfil.notas = dict(list(perfil.notas.items())[-MAX_NOTAS:])
            perfil.actualizado_en = _ahora_iso()
            self._guardar_en_disco()
            return perfil

    async def reset(self, id_user: int) -> None:
        """Borra toda la memoria de un usuario (para pruebas: 'empezar
        de cero' sin tocar la de otros usuarios)."""
        async with self._lock:
            self._perfiles.pop(id_user, None)
            self._guardar_en_disco()

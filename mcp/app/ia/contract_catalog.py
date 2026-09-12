"""
Catálogo del contrato A2UI-MCP — parte de Guillermo (MCP + modelo de IA).

Carga `contracts/a2ui/a2ui-mcp-contract.yaml` (el contrato que Pablo/Cain/
Juan Pablo y Guillermo acordaron) y expone:

  - CONTRACT: el YAML crudo ya parseado (por si se necesita algo puntual).
  - DATA_REFS / ACTIONS / COMPONENTS: catálogos indexados por nombre.
  - validar_a2ui_json(payload): implementa las reglas de la sección
    "validation.rejectIf" del contrato — la IA NO debe devolver un JSON
    A2UI que las viole.

Por qué existe este módulo (ver notesForMcp en el propio YAML):
    "Guillermo: Tu MCP debe cargar este archivo como catálogo permitido.
    La IA puede usar este contrato para:
      1. Saber qué dataRefs existen.
      2. Saber qué componentes puede generar.
      3. Saber qué acciones puede declarar.
      4. Validar el JSON A2UI antes de devolverlo."

IMPORTANTE (regla del propio contrato): "La IA no debe llamar directamente
a la API para obtener datos reales cuando solo está generando la interfaz."
Es decir, este módulo es solo un catálogo/validador de ESTRUCTURA (qué
dataRefs/acciones/componentes existen) — nunca reemplaza ni llama a
integration/api_client.py. Quien resuelve un dataRef con datos reales es
el frontend (Juan Pablo), llamando directo a la API de Pablo.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger("mcp_ia.contract_catalog")

# mcp/app/ia/contract_catalog.py -> parents[3] es la raíz del repo
# (Reto-Banorte/), donde vive contracts/a2ui/a2ui-mcp-contract.yaml.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CONTRACT_PATH = _REPO_ROOT / "contracts" / "a2ui" / "a2ui-mcp-contract.yaml"
CONTRACT_PATH = Path(os.getenv("A2UI_CONTRACT_PATH", str(_DEFAULT_CONTRACT_PATH)))


def _cargar_contrato(path: Path) -> dict:
    if not path.is_file():
        logger.warning(
            "No se encontró el contrato A2UI en %s. El MCP seguirá funcionando "
            "(ActionPlan de tools sigue igual), pero la validación/catálogo A2UI "
            "quedará vacía hasta que el archivo exista.",
            path,
        )
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


CONTRACT: dict = _cargar_contrato(CONTRACT_PATH)

# Catálogos indexados por nombre, listos para validar/consultar en O(1).
DATA_REFS: dict[str, dict] = CONTRACT.get("dataRefs", {}) or {}
ACTIONS: dict[str, dict] = CONTRACT.get("actions", {}) or {}
COMPONENTS: dict[str, dict] = CONTRACT.get("components", {}) or {}
STATE_KEYS: list[str] = CONTRACT.get("stateKeys", []) or []
RULES: list[str] = CONTRACT.get("rules", []) or []

DATA_REF_NAMES: list[str] = list(DATA_REFS.keys())
ACTION_NAMES: list[str] = list(ACTIONS.keys())
COMPONENT_NAMES: list[str] = list(COMPONENTS.keys())


def dataref_existe(nombre: str) -> bool:
    return nombre in DATA_REFS


def accion_existe(nombre: str) -> bool:
    return nombre in ACTIONS


def componente_existe(nombre: str) -> bool:
    return nombre in COMPONENTS


def _iterar_valores_dinamicos(nodo):
    """Recorre un JSON A2UI y va entregando (ruta, dict) de cada nodo que
    tenga la forma de un "dato dinámico" (trae la clave 'dataRef')."""
    if isinstance(nodo, dict):
        if "dataRef" in nodo:
            yield nodo
        for valor in nodo.values():
            yield from _iterar_valores_dinamicos(valor)
    elif isinstance(nodo, list):
        for item in nodo:
            yield from _iterar_valores_dinamicos(item)


def validar_a2ui_json(payload: dict) -> list[str]:
    """Aplica las reglas de `validation.rejectIf` del contrato sobre un
    JSON A2UI ya generado. Devuelve la lista de motivos de rechazo
    (lista vacía = el JSON pasa la validación estructural).

    Esto NO reemplaza el juicio del modelo ni escanea texto libre en busca
    de saldos/números de cuenta (eso requeriría heurísticas de PII fuera
    de alcance de este catálogo); valida lo que sí se puede verificar de
    forma determinista contra el contrato:
      1. Todo dataRef usado existe en `dataRefs`.
      2. Todo dato dinámico (nodo con "dataRef") declara loading/error.
      3. Toda acción mutante (`actions[...].requiresConfirmation: true`)
         usada en el JSON debe venir acompañada de una confirmación
         explícita (heurística: el payload debe declarar
         `needsConfirmation: true` o un bloque `confirm`/`confirmation`).
    """
    if not isinstance(payload, dict):
        return ["El JSON A2UI no es un objeto"]

    motivos: list[str] = []

    for nodo in _iterar_valores_dinamicos(payload):
        ref = nodo.get("dataRef")
        if isinstance(ref, str) and not dataref_existe(ref):
            motivos.append(f"El JSON A2UI usa un dataRef que no existe en dataRefs: {ref!r}")

        tiene_loading = "loading" in nodo
        tiene_error = "error" in nodo
        if not (tiene_loading and tiene_error):
            motivos.append(
                f"Un dato dinámico (dataRef={ref!r}) no tiene loading/error declarados"
            )

    accion_usada = payload.get("action") or payload.get("actionId")
    if isinstance(accion_usada, str) and accion_usada in ACTIONS:
        requiere_confirmacion = bool(ACTIONS[accion_usada].get("requiresConfirmation"))
        confirma_en_payload = bool(
            payload.get("needsConfirmation") or payload.get("confirm") or payload.get("confirmation")
        )
        if requiere_confirmacion and not confirma_en_payload:
            motivos.append(
                f"La acción mutante {accion_usada!r} requiere confirmación explícita y el JSON no la declara"
            )

    return motivos


def resumen_catalogo() -> dict:
    """Pequeño resumen para logging/debug al arrancar el servidor MCP."""
    return {
        "contrato_path": str(CONTRACT_PATH),
        "contrato_encontrado": bool(CONTRACT),
        "dataRefs": DATA_REF_NAMES,
        "actions": ACTION_NAMES,
        "components": COMPONENT_NAMES,
    }

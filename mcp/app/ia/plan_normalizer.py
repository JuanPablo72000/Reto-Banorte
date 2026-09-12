"""
Normalizador del ActionPlan crudo devuelto por Groq — parte de Guillermo.

Se ejecuta SIEMPRE antes de validar con pydantic (ver ia/groq_client.py).
No inventa datos nuevos: solo empareja lo que el modelo escribió contra el
catálogo de valores que YA existen en schemas.py, y corrige errores de
"ortografía"/formato usando similitud de texto (difflib, stdlib, sin
dependencias nuevas). Si no encuentra una coincidencia razonable, deja el
valor tal cual para que la validación normal de pydantic decida qué hacer.

MIGRACIÓN A BASE DE DATOS REAL: con IDs enteros y `response_format`
json_schema estricto, el modelo ya no puede escribir placeholders de texto
en campos numéricos (el schema solo permite integer o null). Por eso
`STEP_ARGUMENT_PLACEHOLDER_DEFAULTS` casi siempre viene vacío ahora — se
conserva la función `_normalizar_step_arguments` igual de genérica (deriva
todo de schemas.py, nunca hardcodea nombres de campo) para que si algún día
se agrega un campo de texto con placeholder canónico, funcione sin tocar
este archivo. El bloque de `STEP_ARGUMENT_REAL_DEFAULTS` sigue siendo la
red de seguridad: si un modelo no respeta el schema y manda un placeholder
inventado en un campo que no lo tiene, cae al valor real de ese campo.
"""

from __future__ import annotations

import difflib
import logging
import re
from typing import Optional

from app.schemas import (
    CANONICAL_ACTION_IDS,
    CANONICAL_INTENTS,
    INTENT_ALIASES,
    STEP_ARGUMENT_PLACEHOLDER_DEFAULTS,
    STEP_ARGUMENT_REAL_DEFAULTS,
    SUGGESTED_ACTION_ARGUMENT_FIELDS,
)
from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATE_IDS, obtener_plantilla

logger = logging.getLogger("mcp_ia.plan_normalizer")

# Qué tan "parecido" tiene que ser un token a la palabra PLACEHOLDER para
# considerarlo un intento fallido de placeholder (typo, guiones raros, etc.)
_UMBRAL_SIMILITUD_PLACEHOLDER = 0.6
# Qué tan parecido tiene que ser un intent/action_id a uno del catálogo para
# autocorregirlo. Debe ser lo bastante alto para atrapar SOLO typos/sinónimos
# casi idénticos (ej. "suggest_view_contacts" -> "suggest_view_accounts",
# ratio ~0.86) y NUNCA "corregir" una categoría semánticamente distinta que
# el modelo inventó de buena fe (ej. "suggest_open_settings" tiene ratio
# ~0.65 contra "suggest_view_transactions" — con 0.55 caía adentro y
# generaba botones con action_id/label/tool desalineados). Con 0.55 el
# fuzzy-match "corregía" cosas que no debía; con este umbral esos casos
# pasan intactos (y de todas formas action_id no está restringido por un
# enum en pydantic, así que dejarlos tal cual es seguro).
_UMBRAL_SIMILITUD_ETIQUETA = 0.75


def _parece_intento_de_placeholder(valor) -> bool:
    """True si 'valor' parece un placeholder mal escrito (typo, mayúsculas
    raras, guiones bajos de más/menos), aunque no calce exacto con
    "PLACEHOLDER"."""
    if not isinstance(valor, str) or not valor.strip():
        return False
    tokens = [t for t in re.split(r"[_\W]+", valor.upper()) if t]
    return any(
        difflib.SequenceMatcher(None, token, "PLACEHOLDER").ratio() >= _UMBRAL_SIMILITUD_PLACEHOLDER
        for token in tokens
    )


def _normalizar_por_catalogo(valor: str, catalogo: list[str], umbral: float) -> str:
    """Si 'valor' no está exacto en 'catalogo', busca el más parecido por
    similitud de texto. Si nada cruza el umbral, regresa 'valor' sin tocar."""
    if not isinstance(valor, str) or not valor.strip():
        return valor
    if valor in catalogo:
        return valor

    catalogo_lower = [c.lower() for c in catalogo]
    coincidencias = difflib.get_close_matches(valor.strip().lower(), catalogo_lower, n=1, cutoff=umbral)
    if not coincidencias:
        return valor

    corregido = catalogo[catalogo_lower.index(coincidencias[0])]
    if corregido != valor:
        logger.info("Autocorregido por similitud: %r -> %r", valor, corregido)
    return corregido


def normalizar_intent(intent: Optional[str]) -> str:
    if not intent or not str(intent).strip():
        return "provide_overview"

    clave = str(intent).strip().lower()
    if clave in INTENT_ALIASES:
        return INTENT_ALIASES[clave]

    return _normalizar_por_catalogo(intent, CANONICAL_INTENTS, _UMBRAL_SIMILITUD_ETIQUETA)


def normalizar_action_id(action_id: Optional[str]) -> Optional[str]:
    if not action_id:
        return action_id
    return _normalizar_por_catalogo(action_id, CANONICAL_ACTION_IDS, _UMBRAL_SIMILITUD_ETIQUETA)


def normalizar_accessibility_template(template_id: Optional[str]) -> str:
    """La IA solo elige un id de plantilla (nunca valores sueltos). Si
    viene vacío o mal escrito, se autocorrige contra el catálogo de
    app/ia/accessibility_templates.py; si no hay coincidencia razonable,
    cae en 'default' (nunca se inventa un id fuera del catálogo)."""
    if not template_id or not str(template_id).strip():
        return "default"
    corregido = _normalizar_por_catalogo(str(template_id), ACCESSIBILITY_TEMPLATE_IDS, _UMBRAL_SIMILITUD_ETIQUETA)
    return corregido if corregido in ACCESSIBILITY_TEMPLATE_IDS else "default"


def _aplicar_valores_fijos_de_plantilla(accessibility: dict, template_id: str) -> dict:
    """Pisa SOLO los campos de senior_adaptations/visual_impairment_adaptations
    que también existen en el catálogo fijo (accessibility_templates.py),
    copiando el valor literal de la plantilla — nunca el que haya puesto el
    modelo (Groq o Gemini). El resto de campos que exige el schema
    (row_height, show_icons, show_balance_prominent, field_labels,
    audio_description, audio_confirmation) NO está en el catálogo: son
    contextuales a cada paso (ej. "show_balance_prominent" solo tiene
    sentido en el paso de balance), así que se dejan tal cual los decidió
    el modelo.

    Esto resuelve la contradicción entre la regla 6 del prompt (le pide al
    modelo que rellene font_scale/button_size/high_contrast/audio_cue "a
    mano", coherentes con la plantilla) y la regla 13 (esos mismos valores
    YA están fijos por plantilla y nunca deberían inventarse): el modelo
    puede seguir escribiendo algo ahí porque el schema strict lo requiere,
    pero lo que se guarda de verdad siempre es el valor exacto del
    catálogo, así nunca hay desajuste (ej. 1.8 vs 1.75 en low_vision)."""
    plantilla = obtener_plantilla(template_id)
    accessibility = dict(accessibility)

    senior = accessibility.get("senior_adaptations")
    if isinstance(senior, dict):
        senior = dict(senior)
        senior["font_scale"] = plantilla["font_scale"]
        senior["button_size"] = plantilla["size"]
        accessibility["senior_adaptations"] = senior

    visual = accessibility.get("visual_impairment_adaptations")
    if isinstance(visual, dict):
        visual = dict(visual)
        visual["high_contrast"] = plantilla["high_contrast"]
        visual["audio_cue"] = plantilla["audio_cue"]
        accessibility["visual_impairment_adaptations"] = visual

    return accessibility


def _normalizar_step_arguments(arguments: dict) -> dict:
    """En 'steps', lo desconocido debe caer siempre en el valor "vacío"
    correcto de ESE campo (placeholder canónico de texto si existe, o si
    no, el default real del campo — None para IDs/fechas, "MXN" para
    currency, 20 para limit, "app" para method, etc.)."""
    if not isinstance(arguments, dict):
        return arguments

    normalizados = dict(arguments)

    # 1) Campos con placeholder canónico de texto (normalmente vacío tras
    #    la migración a IDs enteros; se deja por compatibilidad futura).
    for campo, placeholder_canonico in STEP_ARGUMENT_PLACEHOLDER_DEFAULTS.items():
        valor = normalizados.get(campo)
        if _parece_intento_de_placeholder(valor) and valor != placeholder_canonico:
            logger.info(
                "Placeholder normalizado en steps.arguments['%s']: %r -> %r",
                campo, valor, placeholder_canonico,
            )
            normalizados[campo] = placeholder_canonico

    # 2) Campos sin placeholder canónico (id_user, id_account, currency,
    #    limit, method, etc.): si el valor parece un placeholder inventado
    #    (un modelo que no respetó el schema estricto), cae al valor real
    #    por defecto del campo en vez de quedarse con basura.
    for campo, valor_real in STEP_ARGUMENT_REAL_DEFAULTS.items():
        valor = normalizados.get(campo)
        if _parece_intento_de_placeholder(valor):
            logger.info(
                "Placeholder inválido en steps.arguments['%s'] (campo sin placeholder canónico): %r -> %r",
                campo, valor, valor_real,
            )
            normalizados[campo] = valor_real
    return normalizados


def _normalizar_suggested_action_arguments(arguments: dict) -> dict:
    """En 'suggested_actions[].arguments' la convención es null para lo
    desconocido (nunca placeholders de texto). Si el modelo metió un
    placeholder de texto aquí por error, se convierte a null."""
    if not isinstance(arguments, dict):
        return arguments

    normalizados = dict(arguments)
    for campo in SUGGESTED_ACTION_ARGUMENT_FIELDS:
        valor = normalizados.get(campo)
        if _parece_intento_de_placeholder(valor):
            logger.info(
                "Placeholder inválido en suggested_action.arguments['%s']: %r -> null",
                campo, valor,
            )
            normalizados[campo] = None
    return normalizados


def normalizar_plan(data: dict) -> dict:
    """Punto de entrada: recibe el dict crudo (ya parseado de JSON) que
    devolvió Groq y regresa una copia con placeholders/intent/action_id
    autocorregidos contra el catálogo de schemas.py. No muta 'data'."""
    if not isinstance(data, dict):
        return data

    normalizado = dict(data)
    normalizado["intent"] = normalizar_intent(normalizado.get("intent"))
    normalizado["accessibility_template"] = normalizar_accessibility_template(
        normalizado.get("accessibility_template")
    )

    steps = normalizado.get("steps")
    if isinstance(steps, list):
        nuevos_steps = []
        for step in steps:
            if isinstance(step, dict):
                step = dict(step)
                if isinstance(step.get("arguments"), dict):
                    step["arguments"] = _normalizar_step_arguments(step["arguments"])
                if isinstance(step.get("accessibility"), dict):
                    step["accessibility"] = _aplicar_valores_fijos_de_plantilla(
                        step["accessibility"], normalizado["accessibility_template"]
                    )
            nuevos_steps.append(step)
        normalizado["steps"] = nuevos_steps

    suggested_actions = normalizado.get("suggested_actions")
    if isinstance(suggested_actions, list):
        nuevas_acciones = []
        for accion in suggested_actions:
            if isinstance(accion, dict):
                accion = dict(accion)
                accion["action_id"] = normalizar_action_id(accion.get("action_id"))
                if isinstance(accion.get("arguments"), dict):
                    accion["arguments"] = _normalizar_suggested_action_arguments(accion["arguments"])
            nuevas_acciones.append(accion)
        normalizado["suggested_actions"] = nuevas_acciones

    return normalizado

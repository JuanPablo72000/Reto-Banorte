"""
Normalizador del ActionPlan crudo devuelto por la IA — parte de Guillermo.

Se ejecuta SIEMPRE antes de validar con pydantic (ver ia/ia_client.py).
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
    ACTION_ID_ALIASES,
    CANONICAL_ACTION_IDS,
    CANONICAL_INTENTS,
    DEFAULT_UI_HINT_BY_TOOL,
    INTENT_ALIASES,
    STEP_ARGUMENT_PLACEHOLDER_DEFAULTS,
    STEP_ARGUMENT_REAL_DEFAULTS,
    SUGGESTED_ACTION_ARGUMENT_FIELDS,
    TOOL_ALIASES,
    TOOL_NAMES,
    BadgeTone,
    ComponentVariant,
    IconType,
    Priority,
    UIHint,
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

# Umbral para corregir el campo "tool" (steps y suggested_actions) contra
# TOOL_NAMES. Es deliberadamente ALTO (0.8): una tool equivocada ejecuta el
# endpoint equivocado (peor que fallar en validación), así que aquí solo
# entran typos casi idénticos ("get_transaction" -> "get_transactions",
# ratio 0.97). Todo lo semántico (intents escritos como tool, atajos como
# "get_card_statements") va por TOOL_ALIASES exacto, porque por similitud
# pura caería en la tool equivocada ("get_card_statements" es 0.848
# parecido a "get_statements" y solo 0.844 a "get_credit_card_statements",
# aunque significa lo segundo).
_UMBRAL_SIMILITUD_TOOL = 0.8

# Tools que implican movimiento real de dinero (regla 3 del prompt): si
# algún step las usa, needs_confirmation se fuerza a true aunque el
# modelo lo haya dejado en false.
_TOOLS_QUE_REQUIEREN_CONFIRMACION = ("prepare_transfer", "confirm_transfer")

_UI_HINTS = [h.value for h in UIHint]
_ICONOS = [i.value for i in IconType]
_VARIANTES = [v.value for v in ComponentVariant]
_TONOS = [t.value for t in BadgeTone]
_PRIORIDADES = [p.value for p in Priority]


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


def _clave(valor: object) -> str:
    """Normaliza llaves para comparar: minúsculas, espacios/guiones a
    guion bajo, sin bordes."""
    return re.sub(r"[\s\-]+", "_", str(valor).strip().lower())


def normalizar_action_id(action_id: Optional[str]) -> Optional[str]:
    if not action_id:
        return action_id
    clave = _clave(action_id)
    if clave in ACTION_ID_ALIASES:
        corregido = ACTION_ID_ALIASES[clave]
        if corregido != action_id:
            logger.info("Action_id mapeado por alias: %r -> %r", action_id, corregido)
        return corregido
    return _normalizar_por_catalogo(action_id, CANONICAL_ACTION_IDS, _UMBRAL_SIMILITUD_ETIQUETA)


def normalizar_tool(tool: Optional[str]) -> Optional[str]:
    """Corrige el campo "tool" contra los métodos reales (TOOL_NAMES).

    Orden: exacto -> TOOL_ALIASES (casos semánticos) -> mayor similitud
    (>= 0.8, solo typos). Si nada calza, se deja tal cual para que
    pydantic falle con un error claro en vez de ejecutar otra tool.
    """
    if not tool or not str(tool).strip():
        return tool
    if tool in TOOL_NAMES:
        return tool
    clave = _clave(tool)
    if clave in TOOL_ALIASES:
        corregido = TOOL_ALIASES[clave]
        logger.info("Tool mapeada por alias: %r -> %r", tool, corregido)
        return corregido
    nombre_limpio = _clave(tool)
    exactos = [t for t in TOOL_NAMES if _clave(t) == nombre_limpio]
    if exactos:
        return exactos[0]
    return _normalizar_por_catalogo(tool, TOOL_NAMES, _UMBRAL_SIMILITUD_TOOL)


def normalizar_ui_hint(ui_hint: Optional[str], tool: Optional[str] = None) -> Optional[str]:
    """Corrige "ui_hint" contra UIHint. Si no hay parecido razonable pero
    la tool sí es conocida, cae al ui_hint por defecto de esa tool
    (DEFAULT_UI_HINT_BY_TOOL) en vez de dejar un valor inválido."""
    if ui_hint in _UI_HINTS:
        return ui_hint
    if isinstance(ui_hint, str) and ui_hint.strip():
        corregido = _normalizar_por_catalogo(ui_hint, _UI_HINTS, _UMBRAL_SIMILITUD_ETIQUETA)
        if corregido in _UI_HINTS and corregido != ui_hint:
            return corregido
    if tool in DEFAULT_UI_HINT_BY_TOOL:
        por_defecto = DEFAULT_UI_HINT_BY_TOOL[tool]
        logger.info(
            "ui_hint inválido %r para tool %r, usando default %r", ui_hint, tool, por_defecto
        )
        return por_defecto
    return ui_hint


def normalizar_enum_visual(valor: Optional[str], catalogo: list[str], campo: str) -> Optional[str]:
    """Corrige icon/variant/tone/priority contra su enum. Sin default por
    tool aquí: si no hay parecido, se deja tal cual (pydantic decide)."""
    if valor in catalogo:
        return valor
    if isinstance(valor, str) and valor.strip():
        return _normalizar_por_catalogo(valor, catalogo, _UMBRAL_SIMILITUD_ETIQUETA)
    return valor


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
    modelo (DeepSeek o Gemini). El resto de campos que exige el schema
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
    devolvió la IA y regresa una copia con placeholders/intent/action_id
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
                step["tool"] = normalizar_tool(step.get("tool"))
                step["ui_hint"] = normalizar_ui_hint(step.get("ui_hint"), step.get("tool"))
                if isinstance(step.get("arguments"), dict):
                    step["arguments"] = _normalizar_step_arguments(step["arguments"])
                if isinstance(step.get("visual"), dict):
                    visual = dict(step["visual"])
                    visual["icon"] = normalizar_enum_visual(visual.get("icon"), _ICONOS, "icon")
                    visual["variant"] = normalizar_enum_visual(visual.get("variant"), _VARIANTES, "variant")
                    visual["tone"] = normalizar_enum_visual(visual.get("tone"), _TONOS, "tone")
                    # El default del schema es "none" y la IA casi nunca
                    # elige una animación explícita: sin esto, en la
                    # práctica ningún step se anima nunca. El CSS ya
                    # respeta prefers-reduced-motion / data-reduced-motion,
                    # así que forzar "fade" aquí es seguro incluso para
                    # perfiles con movimiento reducido.
                    if not visual.get("animation") or visual.get("animation") == "none":
                        visual["animation"] = "fade"
                    step["visual"] = visual
                if isinstance(step.get("accessibility"), dict):
                    step["accessibility"] = _aplicar_valores_fijos_de_plantilla(
                        step["accessibility"], normalizado["accessibility_template"]
                    )
            nuevos_steps.append(step)
        normalizado["steps"] = nuevos_steps

        # Regla 3 del prompt: cualquier prepare/confirm_transfer exige
        # confirmación, aunque el modelo haya puesto false.
        tools_usadas = {
            s.get("tool") for s in nuevos_steps if isinstance(s, dict)
        }
        if tools_usadas & set(_TOOLS_QUE_REQUIEREN_CONFIRMACION):
            if normalizado.get("needs_confirmation") is not True:
                logger.info("needs_confirmation forzado a true por step de transferencia")
            normalizado["needs_confirmation"] = True

    suggested_actions = normalizado.get("suggested_actions")
    if isinstance(suggested_actions, list):
        nuevas_acciones = []
        for accion in sugeridas(suggested_actions):
            nuevas_acciones.append(accion)
        normalizado["suggested_actions"] = nuevas_acciones

    return normalizado


def sugeridas(suggested_actions: list) -> list:
    """Normaliza suggested_actions: action_id (alias + similitud), tool e
    ui_hint (igual que en steps), icon/variant/priority, argumentos a null."""
    nuevas_acciones = []
    for accion in suggested_actions:
        if isinstance(accion, dict):
            accion = dict(accion)
            accion["action_id"] = normalizar_action_id(accion.get("action_id"))
            accion["tool"] = normalizar_tool(accion.get("tool"))
            accion["ui_hint"] = normalizar_ui_hint(accion.get("ui_hint"), accion.get("tool"))
            accion["icon"] = normalizar_enum_visual(accion.get("icon"), _ICONOS, "icon")
            accion["variant"] = normalizar_enum_visual(accion.get("variant"), _VARIANTES, "variant")
            accion["priority"] = normalizar_enum_visual(accion.get("priority"), _PRIORIDADES, "priority")
            if isinstance(accion.get("arguments"), dict):
                accion["arguments"] = _normalizar_suggested_action_arguments(accion["arguments"])
        nuevas_acciones.append(accion)
    return nuevas_acciones
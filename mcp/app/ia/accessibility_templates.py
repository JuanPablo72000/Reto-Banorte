"""
Catálogo de plantillas de accesibilidad — parte de Guillermo (MCP + modelo de IA).

Por qué existe este módulo:
  La IA NUNCA debe inventar valores de accesibilidad sueltos (un
  font_scale cualquiera, un color cualquiera). En vez de eso, aquí se
  define un catálogo FIJO de plantillas -> la IA solo elige un id de este
  diccionario (como ya hace con "intent" o "action_id" en schemas.py), y
  el front (Juan Pablo) aplica los valores reales de esa plantilla sobre
  los tokens de components/ui.

Cómo agregar un caso nuevo (una condición, un tamaño de letra, etc.):
  1. Agrega un valor al enum AccessibilityTemplateId.
  2. Agrega su entrada correspondiente en ACCESSIBILITY_TEMPLATES.
  Nada más: el JSON Schema (schemas.py), el normalizador
  (plan_normalizer.py) y el ActionPlan ya generan sus listas/validaciones
  a partir de este archivo, así que no hay que tocarlos.

"size" usa EXACTAMENTE los mismos 3 valores ("sm"/"md"/"lg") que el prop
`size` de Button/IconButton en frontend/src/components/ui: el frontend
puede pasarlo directo (`<Button size={plantilla.size}>`) sin traducir
nada. "color_filter" es una pista para el frontend (qué filtro CSS/SVG de
simulación de daltonismo invertir aplicar, no un valor que la IA calcule).
"""

from __future__ import annotations

from enum import Enum


class AccessibilityTemplateId(str, Enum):
    DEFAULT = "default"
    SENIOR = "senior"
    LOW_VISION = "low_vision"
    BLIND_SCREEN_READER = "blind_screen_reader"
    COLOR_BLIND_PROTANOPIA = "color_blind_protanopia"
    COLOR_BLIND_DEUTERANOPIA = "color_blind_deuteranopia"
    COLOR_BLIND_TRITANOPIA = "color_blind_tritanopia"
    MOTOR_IMPAIRMENT = "motor_impairment"
    COGNITIVE_IMPAIRMENT = "cognitive_impairment"
    LOW_LITERACY = "low_literacy"


# Fuente única de verdad. Cada plantilla trae SIEMPRE las mismas 9 llaves
# para que el frontend pueda aplicarlas sin checar cuáles existen.
ACCESSIBILITY_TEMPLATES: dict[str, dict] = {
    AccessibilityTemplateId.DEFAULT.value: {
        "label": "Predeterminada",
        "font_scale": 1.0,
        "high_contrast": False,
        "dark_mode": False,
        "reduced_motion": False,
        "large_targets": False,
        "plain_language": False,
        "size": "md",
        "color_filter": "none",  # none | protanopia | deuteranopia | tritanopia
        "audio_cue": False,
    },
    AccessibilityTemplateId.SENIOR.value: {
        "label": "Adulto mayor",
        "font_scale": 1.5,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": True,
        "large_targets": True,
        "plain_language": True,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": False,
    },
    AccessibilityTemplateId.LOW_VISION.value: {
        "label": "Baja visión",
        "font_scale": 1.75,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": True,
        "large_targets": True,
        "plain_language": False,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": True,
    },
    AccessibilityTemplateId.BLIND_SCREEN_READER.value: {
        "label": "Ceguera / lector de pantalla",
        "font_scale": 1.25,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": True,
        "large_targets": True,
        "plain_language": False,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": True,
    },
    AccessibilityTemplateId.COLOR_BLIND_PROTANOPIA.value: {
        "label": "Daltonismo — protanopia",
        "font_scale": 1.0,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": False,
        "large_targets": False,
        "plain_language": False,
        "size": "md",
        "color_filter": "protanopia",
        "audio_cue": False,
    },
    AccessibilityTemplateId.COLOR_BLIND_DEUTERANOPIA.value: {
        "label": "Daltonismo — deuteranopia",
        "font_scale": 1.0,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": False,
        "large_targets": False,
        "plain_language": False,
        "size": "md",
        "color_filter": "deuteranopia",
        "audio_cue": False,
    },
    AccessibilityTemplateId.COLOR_BLIND_TRITANOPIA.value: {
        "label": "Daltonismo — tritanopia",
        "font_scale": 1.0,
        "high_contrast": True,
        "dark_mode": False,
        "reduced_motion": False,
        "large_targets": False,
        "plain_language": False,
        "size": "md",
        "color_filter": "tritanopia",
        "audio_cue": False,
    },
    AccessibilityTemplateId.MOTOR_IMPAIRMENT.value: {
        "label": "Discapacidad motriz",
        "font_scale": 1.25,
        "high_contrast": False,
        "dark_mode": False,
        "reduced_motion": True,
        "large_targets": True,
        "plain_language": False,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": False,
    },
    AccessibilityTemplateId.COGNITIVE_IMPAIRMENT.value: {
        "label": "Discapacidad cognitiva",
        "font_scale": 1.25,
        "high_contrast": False,
        "dark_mode": False,
        "reduced_motion": True,
        "large_targets": True,
        "plain_language": True,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": False,
    },
    AccessibilityTemplateId.LOW_LITERACY.value: {
        "label": "Baja alfabetización",
        "font_scale": 1.25,
        "high_contrast": False,
        "dark_mode": False,
        "reduced_motion": False,
        "large_targets": True,
        "plain_language": True,
        "size": "lg",
        "color_filter": "none",
        "audio_cue": False,
    },
}

ACCESSIBILITY_TEMPLATE_IDS: list[str] = list(ACCESSIBILITY_TEMPLATES.keys())


def obtener_plantilla(template_id: str) -> dict:
    """Devuelve los valores fijos de una plantilla. Si el id no existe en
    el catálogo (la IA se equivocó y el normalizador no pudo corregirlo),
    cae en 'default' — nunca se inventan valores fuera de este archivo."""
    return ACCESSIBILITY_TEMPLATES.get(
        template_id, ACCESSIBILITY_TEMPLATES[AccessibilityTemplateId.DEFAULT.value]
    )

"""
Cliente de IA (Groq) para el servidor MCP — parte de Guillermo.

VERSIÓN BANORTE ACCESSIBLE + BASE DE DATOS REAL: genera planes enriquecidos
(metadata visual, sugerencias contextuales, adaptaciones por perfil de
usuario, mensajes en lenguaje simple, recomendaciones de accesibilidad)
usando los IDs enteros reales de BancaAdaptativa.Api (IdUser, IdAccount,
IdTransfer...) en vez de los placeholders de texto que se usaban antes de
que existiera el backend de Pablo.

Cambio clave respecto a la versión anterior (placeholders de texto):
  - STEP_ARGUMENTS_SCHEMA (schemas.py) declara los IDs como
    ["integer", "null"]. Con response_format json_schema en modo strict,
    el modelo YA NO PUEDE inventar un placeholder de texto en un campo
    numérico: solo puede dar el entero real o `null`. Por eso el
    SYSTEM_INSTRUCTION de abajo le pide `null` para "no lo sé" en vez de
    "__PLACEHOLDER_...__", tanto en 'steps' como en 'suggested_actions'.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional

import groq
from groq import AsyncGroq
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from app.schemas import ACTION_PLAN_SCHEMA, DEFAULT_UI_HINT_BY_TOOL, TOOL_NAMES, ActionPlan
from app.ia.plan_normalizer import normalizar_plan
from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATES

logger = logging.getLogger("mcp_ia.groq_client")

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_API_KEY_DE_GROQ_AQUI")

# Gemini es un PROVEEDOR DISTINTO con cupo propio (nada que ver con el de
# Groq) — se usa como último recurso de la cadena de fallback, después de
# agotar TODOS los tiers de Groq. Así, cuando Groq se queda sin cupo en
# los 5 modelos (como en los 429 de los logs), todavía queda una salida en
# vez de esperar 40+ segundos o fallar. Combinar proveedores no tiene nada
# de malo: es el mismo patrón de "varios modelos, varios cupos" que ya
# usa MODEL_POOLS, solo que cruzando de API. Si no hay GEMINI_API_KEY en
# el .env, este tier queda vacío y el comportamiento es IDÉNTICO al de
# antes (no rompe nada para quien no configure Gemini).
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODELS: list[str] = (
    [m.strip() for m in os.getenv("GEMINI_MODELS", "gemini-2.5-flash").split(",") if m.strip()]
    if GEMINI_API_KEY
    else []
)
_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# El Schema de Gemini (google.genai.types.Schema) NO es JSON Schema puro:
# no acepta uniones de tipo como ["integer", "null"] (un solo string del
# enum TYPE_UNSPECIFIED/STRING/.../NULL), ni `None` dentro de "enum". Ahí
# se usa "nullable: true" en vez de meter "null" en la lista de "type".
# ACTION_PLAN_SCHEMA (schemas.py) está pensado para el "strict" de Groq
# (JSON Schema real), así que se convierte una sola vez aquí en vez de
# mantener dos schemas a mano.
_JSON_TYPE_A_GEMINI = {
    "object": "OBJECT", "array": "ARRAY", "string": "STRING",
    "number": "NUMBER", "integer": "INTEGER", "boolean": "BOOLEAN",
}


def _a_gemini_schema(nodo):
    if not isinstance(nodo, dict):
        return nodo
    nodo = dict(nodo)
    nodo.pop("additionalProperties", None)

    tipo = nodo.pop("type", None)
    if isinstance(tipo, list):
        tipos_no_null = [t for t in tipo if t != "null"]
        if "null" in tipo:
            nodo["nullable"] = True
        tipo = tipos_no_null[0] if tipos_no_null else "string"
    if tipo is not None:
        nodo["type"] = _JSON_TYPE_A_GEMINI.get(tipo, "STRING")

    if "enum" in nodo:
        nodo["enum"] = [v for v in nodo["enum"] if v is not None]

    if "properties" in nodo:
        nodo["properties"] = {k: _a_gemini_schema(v) for k, v in nodo["properties"].items()}
    if "items" in nodo:
        nodo["items"] = _a_gemini_schema(nodo["items"])
    return nodo


GEMINI_ACTION_PLAN_SCHEMA = _a_gemini_schema(ACTION_PLAN_SCHEMA)

# TIERS DE MODELOS: en Groq el rate limit (RPM/TPM) es POR MODELO, no un cupo
# único para toda la cuenta. Por eso repartir entre modelos distintos da más
# margen real (a diferencia de usar varias cuentas, que sí viola sus términos).
#
# Solo se listan aquí modelos que SÍ pueden generar el ActionPlan (chat +
# JSON schema estricto). Quedan fuera a propósito:
#   - canopylabs/orpheus-* (texto-a-voz, no generan texto/JSON — y este
#     proyecto es explícitamente SIN VOZ, ver resumen-proyecto-banca-personal.md)
#   - whisper-large-v3* (voz-a-texto, no aplica)
#   - meta-llama/llama-prompt-guard-2-* (clasificadores de seguridad, no
#     generan respuestas conversacionales)
#   - groq/compound y groq/compound-mini (modelos agénticos que pueden
#     invocar herramientas internamente antes de responder; no garantizan
#     bien el response_format json_schema estricto que necesitamos aquí)
#
# Cada tier puede tener más de un modelo: si el primero de un tier se queda
# sin cupo, se prueba el siguiente del MISMO tier antes de subir de tier.
MODEL_POOLS: dict[str, list[str]] = {
    # Modelos eficientes: para intents simples (saludo, overview).
    "fast": [
        m.strip()
        for m in os.getenv("GROQ_MODELS_FAST", "qwen/qwen3.8-27b,qwen/qwen3.6-27b").split(",")
        if m.strip()
    ],
    # Default para la mayoría de los casos.
    "balanced": [
        m.strip()
        for m in os.getenv("GROQ_MODELS_BALANCED", "openai/gpt-oss-20b,openai/gpt-oss-safeguard-20b").split(",")
        if m.strip()
    ],
    # Para operaciones sensibles (transferencias) o cuando ya fallaron los
    # modelos más chicos: más capacidad para respetar el schema completo.
    "strong": [
        m.strip()
        for m in os.getenv("GROQ_MODELS_STRONG", "openai/gpt-oss-120b").split(",")
        if m.strip()
    ],
    # Último recurso, proveedor distinto (Gemini). Vacío si no hay
    # GEMINI_API_KEY configurada (ver arriba).
    "gemini": GEMINI_MODELS,
}

# Palabras que indican una operación sensible (dinero moviéndose de verdad):
# ahí preferimos empezar directo con el tier más capaz, aunque sea más lento.
# "transf" cubre transferir/transferencia/transfiere/transferido, etc.
_PALABRAS_SENSIBLES = (
    "transf", "envia", "envío", "envio", "manda", "mandar",
    "pagar", "pago", "confirma", "confirmar", "retiro", "retirar",
)
# Palabras de intents simples/conversacionales: no necesitan razonamiento fuerte.
_PALABRAS_SIMPLES = (
    "hola", "que puedes hacer", "qué puedes hacer", "ayuda", "help",
    "buenos dias", "buenas tardes", "buenas noches",
)

MAX_RETRIES_PER_MODEL = int(os.getenv("GROQ_MAX_RETRIES", "1"))
RETRY_BASE_DELAY_SECONDS = 2.0
# El ActionPlan enriquecido (visual + accessibility + mensajes x4 por step,
# más 2-4 suggested_actions con el mismo bloque de argumentos) genera un JSON
# largo. Sin este límite, Groq usaba un default bajo y el modelo se quedaba
# a la mitad del documento -> "json_validate_failed".
MAX_COMPLETION_TOKENS = int(os.getenv("GROQ_MAX_COMPLETION_TOKENS", "8192"))


def _es_error_de_cupo_agotado(exc: BaseException) -> bool:
    """True si el error de Groq es, en la práctica, un cupo agotado
    (rate limit de tokens o peticiones por minuto) aunque NO haya llegado
    con status HTTP 429.

    Se detectó en pruebas que Groq puede devolver un "tokens per minute
    (TPM) exceeded" con status 413 (Payload Too Large) en vez de 429
    cuando el prompt+schema de una sola petición ya excede el cupo del
    modelo. La librería `groq` solo mapea el status 429 a
    `groq.RateLimitError` (ver _client.py:_make_status_error); cualquier
    otro status (400, 401, 403, 404, 409, 413, 422...) que no tenga clase
    específica cae en un `groq.APIStatusError` genérico. Sin este chequeo,
    ese 413 se trataba como error FATAL y abortaba toda la cadena de
    fallback (ver `plan()`), en vez de saltar al siguiente modelo de la
    lista -- que tiene su propio cupo independiente y sí podría responder.
    """
    if isinstance(exc, groq.RateLimitError):
        return True

    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        # El body puede venir como {"error": {"code": ..., "type": ...}}
        # o, si algo aplanó la estructura, directo como {"code": ..., ...}.
        error = body.get("error") if isinstance(body.get("error"), dict) else body
        if isinstance(error, dict):
            if error.get("code") == "rate_limit_exceeded":
                return True
            if error.get("type") == "tokens":
                return True

    return False


def _elegir_tier_inicial(user_message: str) -> str:
    """Heurística simple para decidir con qué tier de modelos empezar.

    No es ciencia exacta: es solo para no gastar el modelo fuerte en un
    saludo, ni arriesgar un schema complejo con un modelo más chico cuando
    hay dinero de por medio.
    """
    texto = (user_message or "").lower()

    if any(palabra in texto for palabra in _PALABRAS_SENSIBLES):
        return "strong"
    if any(palabra in texto for palabra in _PALABRAS_SIMPLES) and len(texto) < 60:
        return "fast"
    return "balanced"


def _construir_orden_modelos(tier_inicial: str) -> list[str]:
    """Arma la lista de modelos a intentar: TODOS los del tier elegido
    primero (para agotar ese cupo combinado), y el resto como fallback en
    orden de capacidad decreciente (para no bajar de calidad de golpe en
    operaciones sensibles), sin repetir modelos."""
    cadenas_fallback = {
        "fast": ["fast", "balanced", "strong", "gemini"],
        "balanced": ["balanced", "strong", "fast", "gemini"],
        "strong": ["strong", "balanced", "fast", "gemini"],
    }
    orden_tiers = cadenas_fallback.get(tier_inicial, ["balanced", "strong", "fast"])

    modelos: list[str] = []
    for tier in orden_tiers:
        for modelo in MODEL_POOLS.get(tier, []):
            if modelo not in modelos:
                modelos.append(modelo)
    return modelos


_TOOL_HINTS_TEXT = "\n".join(f"  - {tool} -> ui_hint por defecto: {hint}" for tool, hint in DEFAULT_UI_HINT_BY_TOOL.items())
_ACCESSIBILITY_TEMPLATES_TEXT = "\n".join(
    f"  - {template_id}: {datos['label']}" for template_id, datos in ACCESSIBILITY_TEMPLATES.items()
)

SYSTEM_INSTRUCTION = f"""\
Eres el módulo de decisión de BANORTE ACCESSIBLE, una app de banca personal con MÁXIMA ACCESIBILIDAD.
Tu objetivo es crear una experiencia inclusiva para TODOS los usuarios: adultos mayores, personas con
discapacidad visual, usuarios con poca experiencia tecnológica, personas con discapacidad motriz, etc.

Tu única salida es un JSON que respete el schema indicado. Nunca respondas texto libre.

Tools disponibles (campo "tool" de cada paso): {", ".join(TOOL_NAMES)}

Pista de "ui_hint" por defecto para cada tool:
{_TOOL_HINTS_TEXT}

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ACCESIBILIDAD BANORTE (OBLIGATORIO):
═══════════════════════════════════════════════════════════════════════════

1. SOLO puedes referenciar las tools listadas arriba.

2. Si falta información, deja "steps" vacío y explica en "response_to_user" qué falta.

3. Cualquier paso que use "prepare_transfer" o "confirm_transfer" implica
   needs_confirmation = true.

4. IMPORTANTE — IDs REALES (enteros) de BancaAdaptativa.Api: "arguments" es
   SIEMPRE un objeto con TODOS los campos (24 en "steps": id_user, id_account,
   id_origin_account, id_session, id_transfer, destination_alias,
   destination_masked, amount, currency, concept, query, date_from, date_to,
   limit, method, status, account_type, category, expense_category,
   direction, search, year, month, id_statement, id_credit_card).
   - Los IDs (id_user, id_account, id_origin_account, id_session, id_transfer,
     id_statement, id_credit_card) son SIEMPRE integer o null. NUNCA inventes
     un ID: si no lo conoces, usa null. NUNCA uses texto como "acc_123" o
     "__PLACEHOLDER__": esos IDs ya no existen, la base de datos real usa
     enteros autoincrementales.
   - "amount" es number (usa 0 si no aplica), "currency" es string (usa
     "MXN" si no aplica), "limit" es integer (usa 20 si no aplica), "method"
     es string (usa "app" si no aplica).
   - Los campos de texto que no conozcas (destination_alias,
     destination_masked, concept, query, date_from, date_to, status,
     account_type, category, expense_category, direction, search) van en
     null. Igual "year" y "month" (integer o null) si no aplican.
   - "status" depende de la tool: 'active'/'blocked' (cuentas/tarjetas),
     'pending'/'pending_confirmation'/'confirmed'/'failed' (transferencias),
     'generated'/'archived' (estados de cuenta), 'active'/'exceeded'
     (presupuestos), 'active'/'paused'/'completed' (metas de ahorro).
   - "account_type" es 'debito' o 'credito' (filtro de get_accounts).
   - "direction" es 'credit' o 'debit' (filtro de transacciones).
   - "category"/"expense_category"/"search" son texto libre para filtrar
     transacciones, presupuestos o categorías de gasto.
   - "year"/"month" se usan para filtrar estados de cuenta (de cuenta o de
     tarjeta) y presupuestos mensuales.
   - "id_statement" se usa solo con get_statement_detail; "id_credit_card"
     se usa con get_credit_cards/get_credit_card_statements.
   - En "suggested_actions", "arguments" SOLO acepta EXACTAMENTE estos 5
     campos: id_user, id_account, id_origin_account, query, limit (nada más).
     Los IDs y limit son integer o null; query es string o null.

5. METADATA VISUAL (obligatoria en cada paso, VARÍALA — nunca repitas el mismo icon/variant/tone/animation en todos los pasos de una respuesta si el contenido es distinto):
   - "visual.icon": elige el MÁS ESPECÍFICO según la tool del paso (no un genérico por defecto):
     * get_user_context -> account | get_accounts/get_account_summary/get_account_detail -> account
     * get_transactions/get_all_transactions -> transaction | get_daily_balance -> balance
     * prepare_transfer/confirm_transfer/get_transfers/get_transfer_detail -> transfer
     * get_reconciliation_status -> search | get_statements/get_statement_detail -> statement
     * get_expense_categories -> category | get_budgets_monthly -> budget
     * get_savings_goals -> goal | get_credit_cards/get_credit_card_statements -> card
     * search_memory_context -> search
     Catálogo COMPLETO (nunca uses uno fuera de esta lista):
     [account, transaction, transfer, balance, search, help, warning, success, info, settings, statement, budget, goal, card, category]
   - "visual.variant": EXACTO al prop `variant` de Button/IconButton del frontend: [primary, secondary, ghost, danger]
     (primary = la acción principal del paso; secondary/ghost = acciones secundarias; danger SOLO para eliminar/confirmar algo irreversible)
   - "visual.tone": EXACTO al tono de Badge/Tag del frontend: [success, warning, danger, info, neutral] o null si el elemento no es un badge/tag.
     Úsalo con sentido: success si el dato es positivo/completado (saldo a favor, transferencia confirmada), warning si hay algo que atender (presupuesto cerca del límite, pendiente de confirmación), danger si hay un problema/rechazo, info para datos neutros informativos.
   - "visual.emphasis": "highlighted" para el dato más importante de la respuesta (ej. el saldo total, el monto de una transferencia), "subtle" para datos secundarios/contextuales, "normal" para el resto. NO pongas "normal" en todo.
   - "visual.animation": elige SIEMPRE algo distinto de "none" salvo que el usuario tenga movimiento reducido activo (accessibility_template lo indica). Regla práctica:
     * "fade": el default para la mayoría de los pasos informativos (cuentas, transacciones, saldos, listados).
     * "slide": para confirmaciones, alertas, pasos que requieren atención inmediata del usuario (prepare_transfer/confirm_transfer, pendientes, errores).
     * "pulse": SOLO para lo más urgente/destacado de la respuesta (ej. una alerta crítica o el paso con priority=high).
     * "none": únicamente si el usuario pidió explícitamente movimiento reducido.
   NUNCA mandes un color hex, una clase de Tailwind ni un tamaño en "visual":
   el tamaño (sm/md/lg) SIEMPRE lo decide la plantilla de accesibilidad
   (punto 13 más abajo), nunca tú por elemento.

6. ACCESIBILIDAD (obligatoria en cada paso):
   - "accessibility.aria_label": etiqueta corta para lectores de pantalla
   - "accessibility.screen_reader_text": texto completo descriptivo
   - "accessibility.focusable": true (casi siempre)
   - "accessibility.plain_language_text": versión simple del texto
   - "accessibility.tooltip": ayuda contextual
   - "accessibility.keyboard_shortcut": atajo (ej: "Alt+C")
   - "accessibility.senior_adaptations": {{"font_scale": 1.5, "button_size": "lg"}}
     — NUNCA null: rellena SIEMPRE los 6 campos con valores concretos,
     coherentes con la "accessibility_template" elegida (regla 13). Incluso
     con template "default" van valores razonables (ver EJEMPLO 1).
   - "accessibility.visual_impairment_adaptations": {{"high_contrast": true, "audio_cue": true}}
     — mismo criterio: NUNCA null, siempre los 4 campos con valores concretos.

7. MENSAJES ADAPTADOS (obligatorio en cada paso):
   - "messages.default": mensaje normal
   - "messages.senior": mensaje para adultos mayores (más simple, más claro)
   - "messages.visual_impairment": mensaje optimizado para lectores de pantalla
   - "messages.cognitive_impairment": mensaje ultra-simple, paso a paso

8. SUGERENCIAS CONTEXTUALES (obligatorio en ActionPlan):
   Genera 2-4 "suggested_actions" relacionadas con la intención del usuario.
   Ejemplo: si el usuario ve transacciones, sugiere:
   - "Ver balance actual"
   - "Hacer una transferencia"
   - "Descargar estado de cuenta"
   Cada sugerencia debe tener:
   - action_id: único (ej: "suggest_view_balance")
   - label: texto del botón
   - description: qué hace
   - tool: qué tool invocar
   - reason: por qué lo sugerimos
   - icon: el más específico según la tool que invoca (misma lista completa del punto 5: [account, transaction, transfer, balance, search, help, warning, success, info, settings, statement, budget, goal, card, category]). NUNCA uses "info" por default si hay un ícono más específico disponible.
   - variant: [primary, secondary, ghost, danger] — primary SOLO en la sugerencia más relevante (como máximo una por respuesta), danger SOLO si es destructiva, el resto secondary o ghost
   - priority: "high", "medium", "low"

9. CONSEJOS CONTEXTUALES (obligatorio en ActionPlan):
   Genera 1-3 "contextual_tips" útiles para el usuario.
   Ejemplo: "Revisa tus gastos del mes para identificar oportunidades de ahorro"

10. RECOMENDACIONES DE ACCESIBILIDAD (obligatorio en ActionPlan):
    Genera 1-2 "accessibility_recommendations" basadas en el contexto.
    Ejemplo: "Activa el modo de alto contraste para mejor visibilidad"

11. LENGUAJE SIMPLE (obligatorio en ActionPlan):
    - "response_to_user_plain_language": versión ultra-simple del mensaje principal
    - Usa palabras cotidianas, frases cortas, evita tecnicismos

12. TEMA VISUAL (obligatorio en ActionPlan):
    Sugiere un "visual_theme" coherente:
    - primary_color: "#0078D4" (azul Banorte)
    - accent_color: "#FFB900" (dorado)
    - icon_style: "outlined" o "filled"

13. PLANTILLA DE ACCESIBILIDAD (obligatorio en ActionPlan, campo
    "accessibility_template"): elige EXACTAMENTE UN id de este catálogo
    fijo (nunca inventes valores de font_scale, colores, etc.: esos ya
    están definidos por plantilla en el código, tú solo eliges CUÁL usar):
{_ACCESSIBILITY_TEMPLATES_TEXT}
    Elige según lo que el usuario pida o su perfil conocido (contexto). La
    señal casi NUNCA viene con el nombre técnico de la condición: viene
    escondida en una queja, una anécdota o una descripción del síntoma.
    Lee la CAUSA real, no solo la palabra más llamativa del mensaje:

    - "color_blind_*" (protanopia/deuteranopia/tritanopia): la queja es
      específicamente sobre CONFUNDIR colores entre sí (rojo/verde,
      azul/amarillo, "no distingo si el botón es rojo o verde", "se me ven
      igual", "no sé si salió bien o mal por el color") — el usuario SÍ ve
      el texto y los botones, el problema es solo el color.
      Si nombra el tipo (protanopia/deuteranopia/tritanopia), usa ese id.
      Si dice "daltónico" sin especificar o la pista es solo rojo/verde
      (el par más común), usa "color_blind_deuteranopia".
      Si la pista es azul/amarillo, usa "color_blind_tritanopia".
      NO uses "low_vision" para esto: "low_vision" es cuando el problema
      es agudeza visual en general (todo se ve borroso/chico/necesita
      MÁS contraste global), no una confusión puntual de colores.

    - "senior": el mensaje trae CUALQUIERA de estas pistas aunque nunca
      diga "adulto mayor" ni una edad: alguien más le instaló o configuró
      la app (nieto/a, hijo/a, sobrino/a), menciona lentes/anteojos junto
      con letra chica, un tono de trato formal-anticuado ("disculpe la
      molestia", "joven", "buenas tardes"), o pide que le expliquen paso
      a paso algo simple sin haber mostrado bajo nivel de lectura.

    - "low_vision": agudeza visual reducida en general (visión borrosa,
      "no veo bien de un ojo/de los dos", pide MUCHO más tamaño de letra
      Y más contraste a la vez, sin mencionar colores específicos ni ser
      claramente un tema de edad).

    - "blind_screen_reader": usa o pide lector de pantalla, o dice
      directamente que es ciego/a.

    - "motor_impairment": temblor, artritis, dificultad para dar clic
      preciso, "le atino al botón de al lado", dedos que se resbalan —
      aunque el mensaje empiece quejándose de "la app está rara" y la
      causa motriz venga solo al final o de pasada.

    - "cognitive_impairment": la dificultad es de ORIENTACIÓN o MEMORIA
      dentro de la app, no de vocabulario: "me pierdo", "se me olvida qué
      estaba buscando", "no sé cómo regresé", "se me hace un lío todo
      junto", pide que se simplifique la pantalla por saturación de
      información. Esto es DISTINTO de no entender palabras — si el
      usuario se pierde/confunde navegando aunque entienda las palabras,
      es "cognitive_impairment", no "low_literacy" ni "default".

    - "low_literacy": el problema es de VOCABULARIO o lectura ("no fui
      mucho a la escuela", "no le entiendo a esa palabra rara", pide que
      le expliquen un término con palabras sencillas) — el usuario
      entiende bien dónde está parado, solo no entiende el término.

    - Si el mensaje trae VARIAS señales encimadas (ej. visión + motriz +
      letra chica en un solo mensaje desordenado), elige la que domine la
      queja o, si no hay una claramente principal, la más limitante para
      seguir usando la app en ese momento (visión > motriz > cognitiva),
      y menciona las demás en "accessibility_recommendations".
    - Si de verdad no hay ninguna señal -> "default".
    Esta elección NO cambia con cada paso: aplica a todo el ActionPlan.

14. MEMORIA DE USUARIO (si el "context" trae la llave "memoria_usuario"):
    El caller (mcp_server / PlannerConMemoria, ver app/ia/user_memory.py)
    puede mandar dentro del "context" un bloque así:
      "memoria_usuario": {{
        "accessibility_template_previo": "color_blind_deuteranopia",
        "clics_frecuentes": {{"prepare_transfer": 5, "get_transactions": 2}},
        "intents_recientes": ["make_transfer", "view_balance"]
      }}
    Esto es lo que YA SABEMOS del usuario de turnos anteriores, NO algo
    que él esté diciendo en este mensaje. Reglas para usarlo:

    - "accessibility_template_previo" distinto de "default": ÚSALO como
      "accessibility_template" de esta respuesta, AUNQUE el mensaje
      actual no repita ni mencione la condición. NUNCA vuelvas a
      "default" solo porque el mensaje de este turno habla de otra cosa
      (ej. una transferencia) — la memoria existe justamente para que el
      usuario no tenga que repetir "soy daltónico" cada vez que pide
      algo. Solo cámbialo si el mensaje actual: (a) pide explícitamente
      quitar/cambiar el ajuste, o (b) da una señal clara de una condición
      DISTINTA a la guardada (ver regla 13 para identificarla).
    - "clics_frecuentes": úsalo solo como pista de qué le importa al
      usuario para priorizar "suggested_actions" (la función más usada
      puede llevar variant="primary" o priority="high" si tiene sentido
      con la intención actual). NUNCA cambia "accessibility_template" ni
      "intent" por sí solo.
    - "intents_recientes": son los últimos intents del usuario, solo
      para dar continuidad en "contextual_tips" si aplica (ej. si acaba
      de ver su balance y ahora pregunta por transferencias, puedes
      conectarlo). No repitas esto como si fuera el mensaje actual.
    - Si "memoria_usuario" no viene en el context, trátalo como si no
      hubiera memoria previa (usuario nuevo): aplica solo la regla 13.

15. NUNCA inventes datos financieros reales (saldos, montos de
    transacciones, fechas de movimientos, estados de transferencias) en
    "response_to_user", "response_to_user_plain_language" ni en ningún
    campo de "messages". Tú SOLO planeas qué tool llamar (campo "steps");
    NO ejecutas la tool ni conoces su resultado real — ese dato lo trae
    después quien sí ejecute get_daily_balance / get_transactions /
    get_accounts / get_reconciliation_status. Si no tienes el valor real
    en "contexto" (memoria_usuario) o porque el USUARIO lo escribió
    explícitamente en su mensaje (ej. un monto que él mismo quiere
    transferir), describe la acción en términos genéricos, SIN cifra:
    ✅ "Aquí tienes tu saldo actual" / "Aquí están tus movimientos recientes"
    ❌ "Tu saldo actual es $5,000.00 MXN" (número inventado — GRAVE, sobre
       todo en "visual_impairment" porque el lector de pantalla lo lee
       como un hecho).
    La única excepción es un monto que el propio usuario dio en su mensaje
    (ej. "transferir $500 a mi hermano" -> sí puedes repetir "$500.00 MXN"
    porque es un dato que él mismo aportó, no uno que tú "sabes" de la cuenta).

═══════════════════════════════════════════════════════════════════════════
EJEMPLOS DE RESPUESTAS ENRIQUECIDAS (con IDs reales, enteros):
═══════════════════════════════════════════════════════════════════════════

EJEMPLO 0: Usuario quiere ver su saldo (contexto: id_user=1, id_account=1)
-- OJO: el modelo NO conoce el saldo real (no ejecuta get_daily_balance,
   solo planea llamarla) -> "response_to_user"/"messages" van SIN cifra.
{{
  "intent": "view_balance",
  "steps": [
    {{
      "step_id": "step_1",
      "tool": "get_daily_balance",
      "ui_hint": "summary",
      "arguments": {{
        "id_user": 1, "id_account": 1, "id_origin_account": null,
        "id_session": null, "id_transfer": null, "destination_alias": null,
        "destination_masked": null, "amount": 0.0, "currency": "MXN",
        "concept": null, "query": null, "date_from": null, "date_to": null,
        "limit": 20, "method": "app"
      }},
      "reason": "Obtener el saldo actual de la cuenta",
      "visual": {{"icon": "balance", "variant": "secondary", "tone": "info", "emphasis": "normal", "animation": "fade"}},
      "accessibility": {{
        "aria_label": "Saldo de la cuenta",
        "screen_reader_text": "Muestra el monto disponible en tu cuenta",
        "focusable": true, "keyboard_shortcut": "Alt+B",
        "plain_language_text": "Ver tu saldo actual",
        "tooltip": "Muestra el monto disponible en tu cuenta",
        "senior_adaptations": {{"font_scale": 1.3, "button_size": "lg", "row_height": "large", "show_icons": true, "show_balance_prominent": true, "field_labels": "explicit"}},
        "visual_impairment_adaptations": {{"high_contrast": true, "audio_description": true, "audio_cue": false, "audio_confirmation": false}}
      }},
      "messages": {{
        "default": "Aquí tienes tu saldo actual",
        "senior": "Este es el dinero que tienes disponible ahora",
        "visual_impairment": "Consultando tu saldo actual",
        "cognitive_impairment": "Vamos a ver cuánto dinero tienes"
      }}
    }}
  ],
  "needs_confirmation": false,
  "response_to_user": "Aquí tienes tu saldo actual.",
  "response_to_user_plain_language": "Vamos a ver cuánto dinero tienes.",
  "suggested_actions": [],
  "contextual_tips": [],
  "accessibility_recommendations": [],
  "visual_theme": {{"primary_color": "#0078D4", "accent_color": "#FFB900", "icon_style": "outlined"}},
  "accessibility_template": "default"
}}

EJEMPLO 1: Usuario quiere ver transacciones (contexto: id_user=1, id_account=1)
{{
  "intent": "view_transactions",
  "steps": [
    {{
      "step_id": "step_1",
      "tool": "get_transactions",
      "ui_hint": "table",
      "arguments": {{
        "id_user": 1,
        "id_account": 1,
        "date_from": "2026-08-01",
        "date_to": "2026-08-31",
        "limit": 20,
        "id_origin_account": null,
        "id_session": null,
        "id_transfer": null,
        "destination_alias": null,
        "destination_masked": null,
        "amount": 0.0,
        "currency": "MXN",
        "concept": null,
        "query": null,
        "method": "app"
      }},
      "reason": "Recuperar transacciones del último mes",
      "visual": {{"icon": "transaction", "variant": "secondary", "tone": "info", "emphasis": "normal", "animation": "fade"}},
      "accessibility": {{
        "aria_label": "Tabla de transacciones",
        "screen_reader_text": "Lista de movimientos de tu cuenta del mes pasado",
        "focusable": true,
        "keyboard_shortcut": "Alt+T",
        "plain_language_text": "Ver todos los movimientos de tu dinero",
        "tooltip": "Aquí verás todos los ingresos y gastos del mes",
        "senior_adaptations": {{"font_scale": 1.3, "button_size": "lg", "row_height": "large", "show_icons": true, "show_balance_prominent": false, "field_labels": "explicit"}},
        "visual_impairment_adaptations": {{"high_contrast": true, "audio_description": true, "audio_cue": false, "audio_confirmation": false}}
      }},
      "messages": {{
        "default": "Aquí están tus transacciones de agosto 2026",
        "senior": "Estos son todos los movimientos de tu dinero en agosto",
        "visual_impairment": "Tabla con transacciones de agosto. Usa las flechas para navegar.",
        "cognitive_impairment": "Aquí ves el dinero que entró y salió en agosto"
      }}
    }}
  ],
  "needs_confirmation": false,
  "response_to_user": "Aquí están tus transacciones de agosto 2026. Puedes ver ingresos, gastos y saldos.",
  "response_to_user_plain_language": "Aquí ves todo el dinero que entró y salió de tu cuenta en agosto",
  "suggested_actions": [
    {{
      "action_id": "suggest_view_balance",
      "label": "Ver mi balance actual",
      "description": "Consulta cuánto dinero tienes disponible ahora",
      "tool": "get_daily_balance",
      "arguments": {{"id_user": 1, "id_account": 1, "id_origin_account": null, "query": null, "limit": null}},
      "ui_hint": "summary",
      "reason": "Después de ver transacciones, es útil conocer el saldo actual",
      "icon": "balance",
      "variant": "primary",
      "priority": "high"
    }},
    {{
      "action_id": "suggest_make_transfer",
      "label": "Hacer una transferencia",
      "description": "Envía dinero a otra cuenta",
      "tool": "prepare_transfer",
      "arguments": {{"id_user": 1, "id_account": null, "id_origin_account": 1, "query": null, "limit": null}},
      "ui_hint": "form",
      "reason": "Si viste un pago pendiente, quizás quieras hacer una transferencia",
      "icon": "transfer",
      "variant": "secondary",
      "priority": "medium"
    }}
  ],
  "contextual_tips": [
    "Revisa tus gastos del mes para identificar oportunidades de ahorro",
    "Configura alertas para transacciones mayores a $5,000"
  ],
  "accessibility_recommendations": [
    "Activa el modo de alto contraste para mejor visibilidad en la tabla",
    "Usa las flechas del teclado para navegar entre transacciones"
  ],
  "visual_theme": {{"primary_color": "#0078D4", "accent_color": "#FFB900", "icon_style": "outlined"}},
  "accessibility_template": "default"
}}

EJEMPLO 2: Usuario quiere hacer una transferencia (contexto: id_user=1, id_account=1)
{{
  "intent": "make_transfer",
  "steps": [
    {{
      "step_id": "step_1",
      "tool": "prepare_transfer",
      "ui_hint": "form",
      "arguments": {{
        "id_user": 1,
        "id_origin_account": 1,
        "destination_alias": "Mi hermano",
        "destination_masked": null,
        "amount": 500.0,
        "currency": "MXN",
        "concept": "Regalo de cumpleaños",
        "id_account": null,
        "id_session": null,
        "id_transfer": null,
        "query": null,
        "date_from": null,
        "date_to": null,
        "limit": 20,
        "method": "app"
      }},
      "reason": "Preparar borrador de transferencia para revisión",
      "visual": {{"icon": "transfer", "variant": "primary", "tone": "warning", "emphasis": "highlighted", "animation": "slide"}},
      "accessibility": {{
        "aria_label": "Formulario de transferencia",
        "screen_reader_text": "Formulario para enviar 500 pesos a Mi hermano",
        "focusable": true,
        "keyboard_shortcut": "Alt+T",
        "plain_language_text": "Enviar dinero a otra persona",
        "tooltip": "Revisa los datos antes de confirmar",
        "senior_adaptations": {{"font_scale": 1.5, "button_size": "lg", "row_height": "large", "show_icons": true, "show_balance_prominent": true, "field_labels": "explicit"}},
        "visual_impairment_adaptations": {{"high_contrast": true, "audio_description": false, "audio_cue": false, "audio_confirmation": true}}
      }},
      "messages": {{
        "default": "Vas a enviar $500.00 MXN a Mi hermano. ¿Confirmas?",
        "senior": "Estás enviando 500 pesos a tu hermano. Revisa que esté correcto.",
        "visual_impairment": "Transferencia de 500 pesos a Mi hermano. Presiona Enter para confirmar.",
        "cognitive_impairment": "Vas a mandar 500 pesos. ¿Está bien?"
      }}
    }}
  ],
  "needs_confirmation": true,
  "response_to_user": "Vas a enviar $500.00 MXN a Mi hermano. Por favor confirma la transferencia.",
  "response_to_user_plain_language": "Vas a mandar 500 pesos a tu hermano. Confirma que está bien.",
  "suggested_actions": [
    {{
      "action_id": "suggest_add_to_contacts",
      "label": "Guardar en contactos",
      "description": "Guarda a Mi hermano para futuras transferencias",
      "tool": "search_memory_context",
      "arguments": {{"id_user": 1, "id_account": null, "id_origin_account": null, "query": "Mi hermano", "limit": null}},
      "ui_hint": "form",
      "reason": "Para que sea más fácil la próxima vez",
      "icon": "account",
      "variant": "ghost",
      "priority": "medium"
    }},
    {{
      "action_id": "suggest_view_balance",
      "label": "Ver balance después",
      "description": "Consulta tu saldo después de la transferencia",
      "tool": "get_daily_balance",
      "arguments": {{"id_user": 1, "id_account": 1, "id_origin_account": null, "query": null, "limit": null}},
      "ui_hint": "summary",
      "reason": "Para confirmar que se descontó correctamente",
      "icon": "balance",
      "variant": "secondary",
      "priority": "high"
    }}
  ],
  "contextual_tips": [
    "Guarda contactos frecuentes para hacer transferencias más rápido",
    "Configura transferencias programadas para pagos recurrentes"
  ],
  "accessibility_recommendations": [
    "Usa el lector de pantalla para verificar los montos antes de confirmar",
    "Activa confirmación por voz si tienes discapacidad visual"
  ],
  "visual_theme": {{"primary_color": "#0078D4", "accent_color": "#FFB900", "icon_style": "filled"}},
  "accessibility_template": "senior"
}}

═══════════════════════════════════════════════════════════════════════════
RECUERDA:
═══════════════════════════════════════════════════════════════════════════
✅ SIEMPRE incluye metadata visual y de accesibilidad
✅ SIEMPRE genera 2-4 sugerencias contextuales
✅ SIEMPRE incluye consejos y recomendaciones de accesibilidad
✅ SIEMPRE proporciona mensajes en lenguaje simple
✅ Los IDs (id_user, id_account, id_origin_account, id_session, id_transfer,
   id_statement, id_credit_card)
   son SIEMPRE integer o null. NUNCA inventes un ID ni uses texto/placeholders.
✅ SIEMPRE elige "accessibility_template" del catálogo fijo (nunca inventes
   valores de accesibilidad sueltos, solo el id de la plantilla)
✅ PIENSA como un empresario de Banorte que quiere la MÁXIMA accesibilidad
"""


class GroqPlanner:
    """Wrapper delgado sobre el SDK de Groq para planes enriquecidos."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self._client = AsyncGroq(api_key=api_key or GROQ_API_KEY)
        # Si se fuerza un modelo explícito (compatibilidad con código viejo),
        # lo usamos SIEMPRE de primero y no aplicamos la heurística de tiers.
        self._modelo_forzado = model
        # Último turno (para tests/diagnóstico, ver tests/test_repl_e2e.py):
        # el JSON crudo del modelo ANTES de normalizar y el dict DESPUÉS.
        self.last_raw: Optional[dict] = None
        self.last_normalized: Optional[dict] = None
        self.last_model: Optional[str] = None

    async def _llamar_gemini(self, modelo: str, mensaje_usuario: str) -> str:
        """Misma idea que la llamada a Groq (system+user -> JSON del
        ActionPlan), pero con el SDK de Gemini. Deja que el caller
        (self.plan) capture los errores: relanza tal cual para que el
        except de más abajo decida si es cupo agotado o fatal."""
        response = await _gemini_client.aio.models.generate_content(
            model=modelo,
            contents=mensaje_usuario,
            config=genai_types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=GEMINI_ACTION_PLAN_SCHEMA,
                temperature=0.2,
                max_output_tokens=MAX_COMPLETION_TOKENS,
            ),
        )
        return response.text

    async def plan(self, user_message: str, context: Optional[dict] = None) -> ActionPlan:
        """Pide al modelo un ActionPlan enriquecido con metadata visual y accesibilidad."""

        context = context or {}
        logger.info("Generando plan Banorte Accessible (contexto keys=%s)", list(context.keys()))

        # El modelo no sabe qué día es hoy: sin esto, "mes pasado" o "ayer"
        # quedan en date_from/date_to = null (ver test_local.py caso 1) y la
        # tool trae todo sin filtrar. Se inyecta la fecha real aquí para que
        # la resuelva a rango concreto (ej. hoy 2026-09-12 + "mes pasado" ->
        # date_from=2026-08-01, date_to=2026-08-31).
        hoy = datetime.now().date().isoformat()
        mensaje_usuario = (
            f"Fecha actual: {hoy} (úsala para resolver expresiones relativas "
            f"de tiempo como 'mes pasado', 'ayer' o 'esta quincena' en "
            f"date_from/date_to/year/month).\n"
            f"Contexto disponible (JSON): {json.dumps(context, ensure_ascii=False)}\n\n"
            f"Mensaje/intención del usuario: {user_message}"
        )

        if self._modelo_forzado:
            modelos_a_intentar = [self._modelo_forzado]
        else:
            tier_inicial = _elegir_tier_inicial(user_message)
            modelos_a_intentar = _construir_orden_modelos(tier_inicial)
            logger.info("Tier elegido para este mensaje: %s -> orden de modelos: %s", tier_inicial, modelos_a_intentar)

        ultimo_error: Optional[Exception] = None

        for modelo in modelos_a_intentar:
            for intento in range(1, MAX_RETRIES_PER_MODEL + 1):
                es_gemini = modelo in GEMINI_MODELS
                try:
                    if es_gemini:
                        raw_content = await self._llamar_gemini(modelo, mensaje_usuario)
                    else:
                        response = await self._client.chat.completions.create(
                            model=modelo,
                            messages=[
                                {"role": "system", "content": SYSTEM_INSTRUCTION},
                                {"role": "user", "content": mensaje_usuario},
                            ],
                            response_format={
                                "type": "json_schema",
                                "json_schema": {
                                    "name": "action_plan",
                                    "schema": ACTION_PLAN_SCHEMA,
                                    "strict": True,
                                },
                            },
                            temperature=0.2,  # Bajo: priorizamos JSON exacto sobre creatividad
                            max_completion_tokens=MAX_COMPLETION_TOKENS,
                        )
                        raw_content = response.choices[0].message.content

                    datos_crudos = json.loads(raw_content)
                    datos_normalizados = normalizar_plan(datos_crudos)
                    plan = ActionPlan.model_validate(datos_normalizados)

                    self.last_raw = datos_crudos
                    self.last_normalized = datos_normalizados
                    self.last_model = modelo

                    logger.info(
                        "Plan Banorte Accessible generado con %s: intent=%r pasos=%d sugerencias=%d needs_confirmation=%s",
                        modelo, plan.intent, len(plan.steps), len(plan.suggested_actions), plan.needs_confirmation,
                    )
                    return plan

                except genai_errors.ClientError as exc:
                    # Gemini: 429 = cupo agotado (mismo trato que RateLimitError
                    # de Groq); cualquier otro 4xx es fatal.
                    ultimo_error = exc
                    if getattr(exc, "code", None) == 429:
                        logger.warning("Modelo %s (Gemini) sin cupo (rate limit). Saltando al siguiente modelo...", modelo)
                        break
                    logger.critical("Error no recuperable llamando a Gemini (modelo=%s): %s", modelo, exc)
                    raise

                except genai_errors.ServerError as exc:
                    ultimo_error = exc
                    espera = RETRY_BASE_DELAY_SECONDS * (2 ** (intento - 1))
                    logger.warning(
                        "Modelo %s (Gemini) no disponible (intento %d/%d): %s. Reintentando en %.0fs...",
                        modelo, intento, MAX_RETRIES_PER_MODEL, exc, espera,
                    )
                    await asyncio.sleep(espera)

                except groq.RateLimitError as exc:
                    # El límite de Groq es POR MODELO. Reintentar el mismo modelo no
                    # libera cupo: lo que sirve es saltar de inmediato al siguiente
                    # modelo de la lista, que tiene su propio cupo independiente.
                    ultimo_error = exc
                    logger.warning("Modelo %s sin cupo (rate limit). Saltando al siguiente modelo disponible...", modelo)
                    break  # sale del for de reintentos y pasa al siguiente modelo

                except (groq.InternalServerError, groq.APIConnectionError) as exc:
                    ultimo_error = exc
                    espera = RETRY_BASE_DELAY_SECONDS * (2 ** (intento - 1))
                    logger.warning(
                        "Modelo %s no disponible (intento %d/%d): %s. Reintentando en %.0fs...",
                        modelo, intento, MAX_RETRIES_PER_MODEL, exc, espera,
                    )
                    await asyncio.sleep(espera)

                except groq.BadRequestError as exc:
                    # El JSON del ActionPlan es largo (visual + accessibility + mensajes
                    # x4 por step, suggested_actions, etc.). Si el modelo se corta antes
                    # de cerrar el documento, o arma un JSON que no cumple el schema,
                    # Groq responde json_validate_failed. Es recuperable: reintentamos
                    # (y, si se agotan los intentos, probamos un modelo más capaz).
                    error_code = getattr(getattr(exc, "body", None), "get", lambda *_: None)("code") \
                        if isinstance(getattr(exc, "body", None), dict) else None
                    es_error_de_generacion = error_code == "json_validate_failed" or "json_validate_failed" in str(exc)

                    if not es_error_de_generacion:
                        logger.critical("Error no recuperable llamando a Groq (modelo=%s): %s", modelo, exc)
                        raise

                    ultimo_error = exc
                    espera = RETRY_BASE_DELAY_SECONDS * (2 ** (intento - 1))
                    logger.warning(
                        "Modelo %s no generó un JSON válido (intento %d/%d): %s. Reintentando en %.0fs...",
                        modelo, intento, MAX_RETRIES_PER_MODEL, exc, espera,
                    )
                    await asyncio.sleep(espera)

                except groq.APIStatusError as exc:
                    # Cualquier APIStatusError que NO haya calzado en las
                    # excepciones específicas de arriba (RateLimitError,
                    # InternalServerError, APIConnectionError,
                    # BadRequestError): esto incluye el 413 "tokens per
                    # minute" que Groq no mapea a RateLimitError (ver
                    # _es_error_de_cupo_agotado) y también códigos
                    # genuinamente fatales como 401/403/404/409/422.
                    if _es_error_de_cupo_agotado(exc):
                        ultimo_error = exc
                        logger.warning(
                            "Modelo %s sin cupo (status=%s, disfrazado de rate limit). "
                            "Saltando al siguiente modelo disponible...",
                            modelo, getattr(exc, "status_code", "?"),
                        )
                        break  # sale del for de reintentos y pasa al siguiente modelo

                    logger.critical(
                        "Error no recuperable llamando a Groq (modelo=%s, status=%s): %s",
                        modelo, getattr(exc, "status_code", "?"), exc,
                    )
                    raise

                except Exception as exc:
                    logger.critical("Error no recuperable llamando a Groq (modelo=%s): %s", modelo, exc)
                    raise

            else:
                # Se agotaron los reintentos de este modelo sin ser un rate limit
                # (ese caso ya se manejó arriba con el break).
                logger.error("Modelo %s agotó sus reintentos, probando siguiente modelo si hay...", modelo)
                continue

        logger.critical("Todos los modelos fallaron. Último error: %s", ultimo_error)
        raise ultimo_error if ultimo_error else RuntimeError("No se pudo generar el plan")
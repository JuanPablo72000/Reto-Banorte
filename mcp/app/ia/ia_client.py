"""
Cliente de IA (DeepSeek + Gemini) para el servidor MCP — parte de Guillermo.

VERSIÓN BANORTE ACCESSIBLE + BASE DE DATOS REAL: genera planes enriquecidos
(metadata visual, sugerencias contextuales, adaptaciones por perfil de
usuario, mensajes en lenguaje simple, recomendaciones de accesibilidad)
usando los IDs enteros reales de BancaAdaptativa.Api (IdUser, IdAccount,
IdTransfer...) en vez de los placeholders de texto que se usaban antes de
que existiera el backend de Pablo.

Proveedores (en orden):
  1. DeepSeek (primario, API compatible OpenAI): genera el ActionPlan en
     modo `response_format: json_object`. Como NO hay validación estricta
     del lado del proveedor, el JSON se valida aquí con
     `ActionPlan.model_validate` (schemas.py) después de normalizar.
  2. Gemini (secundario, cupo propio): se usa si DeepSeek se queda sin
     cupo o falla, con el mismo schema convertido (ver _a_gemini_schema).

Cambio clave respecto a la versión anterior (placeholders de texto):
  - STEP_ARGUMENTS_SCHEMA (schemas.py) declara los IDs como
    ["integer", "null"]. El modelo YA NO PUEDE inventar un placeholder
    de texto en un campo numérico: solo puede dar el entero real o
    `null`. Por eso el SYSTEM_INSTRUCTION de abajo le pide `null` para
    "no lo sé" en vez de "__PLACEHOLDER_...__", tanto en 'steps' como en
    'suggested_actions'.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types
from pydantic import ValidationError

from app.schemas import ACTION_PLAN_SCHEMA, DEFAULT_UI_HINT_BY_TOOL, TOOL_NAMES, ActionPlan
from app.ia.plan_normalizer import normalizar_plan
from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATES

logger = logging.getLogger("mcp_ia.ia_client")

# ---------------------------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------------------------
# DeepSeek (primario, API compatible OpenAI). Sin GEMINI/DEEPSEEK keys el
# planner no puede funcionar: falla en plan() con error claro.
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
DEEPSEEK_MODELS: list[str] = [
    m.strip()
    for m in os.getenv("DEEPSEEK_MODELS", "deepseek-chat").split(",")
    if m.strip()
]

# Gemini es un PROVEEDOR DISTINTO con cupo propio — secundario (fallback)
# cuando DeepSeek se queda sin cupo o falla. Si no hay GEMINI_API_KEY en
# el .env, este tier queda vacío (no rompe nada para quien no lo configure).
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
# ACTION_PLAN_SCHEMA (schemas.py) es JSON Schema real, así que se
# convierte una sola vez aquí en vez de mantener dos schemas a mano.
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

# TIERS DE MODELOS: DeepSeek primero (cupo propio), Gemini después (cupo
# propio distinto). Si el primero de la lista se queda sin cupo, se prueba
# el siguiente, que tiene su propio cupo independiente.
MODEL_POOLS: dict[str, list[str]] = {
    "deepseek": DEEPSEEK_MODELS,
    # Secundario, proveedor distinto (Gemini). Vacío si no hay
    # GEMINI_API_KEY configurada (ver arriba).
    "gemini": GEMINI_MODELS,
}

MAX_RETRIES_PER_MODEL = int(os.getenv("IA_MAX_RETRIES", "2"))
RETRY_BASE_DELAY_SECONDS = 2.0
# El ActionPlan enriquecido (visual + accessibility + mensajes x4 por step,
# más 2-4 suggested_actions con el mismo bloque de argumentos) genera un JSON
# largo. Sin este límite, el modelo usaba un default bajo y se quedaba
# a la mitad del documento -> JSON truncado.
MAX_COMPLETION_TOKENS = int(os.getenv("IA_MAX_COMPLETION_TOKENS", "8192"))


def _construir_orden_modelos() -> list[str]:
    """Arma la lista de modelos a intentar: primero TODOS los de DeepSeek
    (primario) y luego los de Gemini (secundario), sin repetir modelos."""
    modelos: list[str] = []
    for tier in ("deepseek", "gemini"):
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

13. VISUALIZACIONES DE DATOS (campo "visualizations" - LA IA TIENE LIBERTAD PARA DECIDIR CUÁNDO INCLUIRLAS):
    Cuando los datos sean complejos o abundantes, GENERA GRÁFICOS O TARJETAS BANCARIAS para ayudar al usuario a comprender mejor la información.
    No es obligatorio incluir visualizaciones en cada respuesta, pero SÍ debes incluirlas cuando:
    - Hay más de 5-10 transacciones y conviene mostrar tendencias de gastos/ingresos
    - Se muestran balances diarios/mensuales y hay patrones visibles
    - Hay categorías de gasto múltiples y conviene comparar proporciones
    - Se muestran presupuestos vs gastos reales
    - Hay metas de ahorro con progreso que puede visualizarse
    - El usuario pide ver sus tarjetas o cuentas de forma visual e interactiva
    - Cualquier conjunto de datos numéricos donde un gráfico ayude más que solo texto/tabla
    
    Tipos de visualización disponibles:
    
    A) GRÁFICOS TRADICIONALES:
       - type: "bar" | "line" | "pie" | "donut" | "area"
         * Usa "bar" para comparar categorías (gastos por categoría, ingresos vs egresos)
         * Usa "line" para mostrar tendencias en el tiempo (balances diarios, gastos mensuales)
         * Usa "pie" o "donut" para mostrar proporciones (distribución de gastos, composición de cartera)
         * Usa "area" para acumulación en el tiempo (ahorro acumulado, gastos acumulados)
       - title: string (título descriptivo del gráfico)
       - data: array de objetos con formato [{{name/label/categoria: string, value/amount/monto: number}}, ...]
         * Asegúrate de que cada objeto tenga UNA clave para la etiqueta (name, label, o categoria)
           y UNA clave numérica para el valor (value, amount, monto, total, etc.)
       - description: string (explicación breve de qué muestra el gráfico y qué insight ofrece)
       - accessibility_label: string (descripción completa para lectores de pantalla)
    
    B) TARJETAS BANCARIAS INTERACTIVAS (tipo "bank_card"):
       Úsalas cuando el usuario pida ver sus tarjetas, cuentas o saldos de forma visual.
       La tarjeta tiene diseño tipo Banorte (rojo/dorado), es interactiva (clic para expandir)
       y muestra información sensible de forma segura.
       
       Estructura requerida:
       - type: "bank_card"
       - title: string (ej: "Tu tarjeta de débito")
       - data: [{{
           cardNumber: string (últimos 4 dígitos o enmascarada, ej: "**** **** **** 1234"),
           holderName: string (nombre del titular),
           expiryDate: string (formato MM/YY),
           balance: string (saldo formateado, ej: "$15,450.00"),
           currency: string (ej: "MXN"),
           cardType: "debit" | "credit",
           bankName: string (opcional, default: "Banorte"),
           additionalInfo: [{{label: string, value: string}}] (opcional, info extra al expandir)
         }}]
       - description: string (explicación de qué tarjeta es)
       - accessibility_label: string (descripción para lectores de pantalla)
    
    Ejemplo de visualización para gastos por categoría:
    {{
      "type": "bar",
      "title": "Gastos del mes por categoría",
      "data": [
        {{"categoria": "Supermercado", "monto": 2000}},
        {{"categoria": "Transporte", "monto": 500}},
        {{"categoria": "Entretenimiento", "monto": 300}}
      ],
      "description": "Tus gastos principales este mes fueron en supermercado, seguidos de transporte.",
      "accessibility_label": "Gráfico de barras: Supermercado $2000 MXN, Transporte $500 MXN, Entretenimiento $300 MXN"
    }}
    
    Ejemplo de visualización para tarjeta bancaria:
    {{
      "type": "bank_card",
      "title": "Tu tarjeta de débito principal",
      "data": [{{
        "cardNumber": "**** **** **** 4532",
        "holderName": "JUAN PÉREZ",
        "expiryDate": "12/26",
        "balance": "$15,450.00",
        "currency": "MXN",
        "cardType": "debit",
        "bankName": "Banorte",
        "additionalInfo": [
          {{"label": "Límite diario", "value": "$9,000.00"}},
          {{"label": "Disponible hoy", "value": "$8,750.00"}}
        ]
      }}],
      "description": "Tarjeta de débito con saldo disponible actualizado.",
      "accessibility_label": "Tarjeta Banorte de débito terminada en 4532, saldo $15,450 pesos mexicanos"
    }}
    
    RECOMENDACIÓN: Incluye al menos 1 visualización cuando muestres datos financieros complejos.
    Para tarjetas/cuentas, usa "bank_card" para una experiencia más interactiva y accesible.
    Esto ayuda especialmente a usuarios con discapacidad cognitiva o baja alfabetización financiera.

14. PLANTILLA DE ACCESIBILIDAD (obligatorio en ActionPlan, campo
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

15. MEMORIA DE USUARIO (si el "context" trae la llave "memoria_usuario"):
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

16. NUNCA inventes datos financieros reales (saldos, montos de
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

EJEMPLO 0-B: Usuario ve transacciones y la IA incluye una visualización (contexto: id_user=1, id_account=1)
-- Aquí la IA DECIDE incluir un gráfico porque hay varias transacciones y conviene mostrar la distribución por categoría.
{{
  "intent": "view_transactions",
  "steps": [
    {{
      "step_id": "step_1",
      "tool": "get_transactions",
      "ui_hint": "table",
      "arguments": {{
        "id_user": 1, "id_account": 1, "id_origin_account": null,
        "id_session": null, "id_transfer": null, "destination_alias": null,
        "destination_masked": null, "amount": 0.0, "currency": "MXN",
        "concept": null, "query": null, "date_from": "2026-08-01", "date_to": null,
        "limit": 20, "method": "app"
      }},
      "reason": "Obtener las últimas transacciones de la cuenta",
      "visual": {{"icon": "transaction", "variant": "secondary", "tone": "info", "emphasis": "normal", "animation": "fade"}},
      "accessibility": {{
        "aria_label": "Transacciones recientes",
        "screen_reader_text": "Lista de movimientos recientes en tu cuenta",
        "focusable": true, "keyboard_shortcut": "Alt+T",
        "plain_language_text": "Tus últimos movimientos",
        "tooltip": "Ver tus transacciones recientes",
        "senior_adaptations": {{"font_scale": 1.3, "button_size": "lg", "row_height": "large", "show_icons": true, "show_balance_prominent": false, "field_labels": "explicit"}},
        "visual_impairment_adaptations": {{"high_contrast": true, "audio_description": true, "audio_cue": false, "audio_confirmation": false}}
      }},
      "messages": {{
        "default": "Aquí están tus transacciones recientes",
        "senior": "Estos son los últimos movimientos de tu cuenta",
        "visual_impairment": "Mostrando tus transacciones recientes",
        "cognitive_impairment": "Vamos a ver los últimos movimientos de tu dinero"
      }}
    }}
  ],
  "needs_confirmation": false,
  "response_to_user": "Aquí están tus transacciones recientes. He incluido un gráfico para que veas cómo se distribuyen tus gastos por categoría.",
  "response_to_user_plain_language": "Estos son tus últimos movimientos. El gráfico muestra en qué gastaste más.",
  "suggested_actions": [],
  "contextual_tips": ["Revisa si hay gastos hormiga que puedas reducir"],
  "accessibility_recommendations": ["Usa el modo alto contraste si tienes dificultad para leer los colores"],
  "visual_theme": {{"primary_color": "#0078D4", "accent_color": "#FFB900", "icon_style": "outlined"}},
  "accessibility_template": "default",
  "visualizations": [
    {{
      "type": "donut",
      "title": "Distribución de gastos por categoría",
      "data": [
        {{"categoria": "Supermercado", "monto": 1500}},
        {{"categoria": "Transporte", "monto": 450}},
        {{"categoria": "Restaurantes", "monto": 600}},
        {{"categoria": "Entretenimiento", "monto": 300}}
      ],
      "description": "Tus gastos se concentran principalmente en supermercado y restaurantes.",
      "accessibility_label": "Gráfico circular: Supermercado $1500 MXN (43%), Restaurantes $600 MXN (17%), Transporte $450 MXN (13%), Entretenimiento $300 MXN (9%)"
    }}
  ]
}}

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


class _CupoAgotado(RuntimeError):
    """El proveedor se quedó sin cupo (rate limit): saltar al siguiente
    modelo de la lista, que tiene su propio cupo independiente."""


class _ErrorFatalIA(RuntimeError):
    """Error no recuperable del proveedor (key inválida, sin saldo,
    modelo inexistente...): abortar, no reintentar."""


class PlannerIA:
    """Planner de IA para planes enriquecidos (DeepSeek primario + Gemini
    secundario). Sin estado entre llamadas salvo last_raw/last_normalized
    (diagnóstico para tests)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        self._deepseek_key = api_key or DEEPSEEK_API_KEY
        # Si se fuerza un modelo explícito, lo usamos SIEMPRE de primero y
        # no aplicamos el orden DeepSeek->Gemini.
        self._modelo_forzado = model
        # Último turno (para tests/diagnóstico, ver tests/test_repl_e2e.py):
        # el JSON crudo del modelo ANTES de normalizar y el dict DESPUÉS.
        self.last_raw: Optional[dict] = None
        self.last_normalized: Optional[dict] = None
        self.last_model: Optional[str] = None

    async def _llamar_deepseek(self, modelo: str, mensaje_usuario: str) -> str:
        """Chat Completions contra DeepSeek (API compatible OpenAI) en modo
        JSON. Deja que el caller (self.plan) capture los errores: relanza
        tal cual para que el except de más abajo decida si es cupo agotado
        (429 -> siguiente modelo) o fatal (401/402/4xx -> abortar)."""
        async with httpx.AsyncClient(base_url=DEEPSEEK_BASE_URL, timeout=120.0) as client:
            resp = await client.post(
                "/chat/completions",
                headers={"Authorization": f"Bearer {self._deepseek_key}"},
                json={
                    "model": modelo,
                    "messages": [
                        {"role": "system", "content": SYSTEM_INSTRUCTION},
                        {"role": "user", "content": mensaje_usuario},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.2,  # Bajo: priorizamos JSON exacto sobre creatividad
                    "max_tokens": MAX_COMPLETION_TOKENS,
                },
            )
        if resp.status_code == 429:
            raise _CupoAgotado(f"DeepSeek sin cupo (429): {resp.text[:200]}")
        if resp.status_code >= 400:
            raise _ErrorFatalIA(f"DeepSeek error {resp.status_code}: {resp.text[:300]}")
        try:
            return resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise _ErrorFatalIA(f"Respuesta inesperada de DeepSeek: {resp.text[:300]}") from exc

    async def _llamar_gemini(self, modelo: str, mensaje_usuario: str) -> str:
        """Misma idea que la llamada a DeepSeek (system+user -> JSON del
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
            modelos_a_intentar = _construir_orden_modelos()
            logger.info("Orden de modelos: %s", modelos_a_intentar)
        if not modelos_a_intentar:
            raise RuntimeError(
                "Sin modelos configurados: define DEEPSEEK_API_KEY "
                "(DEEPSEEK_MODELS) o GEMINI_API_KEY (GEMINI_MODELS) en el .env"
            )

        ultimo_error: Optional[Exception] = None

        for modelo in modelos_a_intentar:
            for intento in range(1, MAX_RETRIES_PER_MODEL + 1):
                es_gemini = modelo in GEMINI_MODELS
                try:
                    if es_gemini:
                        raw_content = await self._llamar_gemini(modelo, mensaje_usuario)
                    else:
                        raw_content = await self._llamar_deepseek(modelo, mensaje_usuario)

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
                    # Gemini: 429 = cupo agotado (se salta al siguiente
                    # modelo); cualquier otro 4xx es fatal.
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

                except _CupoAgotado as exc:
                    # Sin cupo: reintentar el mismo modelo no libera nada;
                    # lo que sirve es saltar al siguiente, con cupo propio.
                    ultimo_error = exc
                    logger.warning("Modelo %s sin cupo. Saltando al siguiente modelo disponible...", modelo)
                    break  # sale del for de reintentos y pasa al siguiente modelo

                except _ErrorFatalIA as exc:
                    logger.critical("Error no recuperable llamando a DeepSeek (modelo=%s): %s", modelo, exc)
                    raise

                except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                    ultimo_error = exc
                    espera = RETRY_BASE_DELAY_SECONDS * (2 ** (intento - 1))
                    logger.warning(
                        "Modelo %s no disponible por red (intento %d/%d): %s. Reintentando en %.0fs...",
                        modelo, intento, MAX_RETRIES_PER_MODEL, exc, espera,
                    )
                    await asyncio.sleep(espera)

                except (ValidationError, json.JSONDecodeError) as exc:
                    # Sin json_schema estricto, el modelo a veces trunca o
                    # malforma el JSON: se reintenta el mismo modelo y, si se
                    # agotan los intentos, se pasa al siguiente.
                    ultimo_error = exc
                    espera = RETRY_BASE_DELAY_SECONDS * (2 ** (intento - 1))
                    logger.warning(
                        "Modelo %s no generó un JSON válido (intento %d/%d): %s. Reintentando en %.0fs...",
                        modelo, intento, MAX_RETRIES_PER_MODEL, str(exc)[:200], espera,
                    )
                    await asyncio.sleep(espera)

                except Exception as exc:
                    logger.critical("Error no recuperable (modelo=%s): %s", modelo, exc)
                    raise

            else:
                # Se agotaron los reintentos de este modelo sin ser un rate limit
                # (ese caso ya se manejó arriba con el break).
                logger.error("Modelo %s agotó sus reintentos, probando siguiente modelo si hay...", modelo)
                continue

        logger.critical("Todos los modelos fallaron. Último error: %s", ultimo_error)
        raise ultimo_error if ultimo_error else RuntimeError("No se pudo generar el plan")


# Compatibilidad con código que importaba el nombre anterior.
GroqPlanner = PlannerIA
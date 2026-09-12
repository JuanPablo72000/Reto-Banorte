"""
Script de prueba local — accesibilidad y daltonismo (casos rebuscados) —
NO es parte del servidor MCP ni del cliente MCP.

Es hermano de test_local.py: mismo mecanismo (llama a GroqPlanner
directo), pero aquí SOLO quedan los 6 casos más difíciles de detectar:
la condición nunca se anuncia con su nombre técnico, viene mezclada con
otra intención (una queja, un trámite bancario) y el mensaje está escrito
como de verdad lo teclearía un adulto mayor desde el celular — sin
acentos, con rodeos, quejándose antes de llegar al punto.

Se quitaron a propósito los casos "de libro" (mensajes cortos que
nombran la condición de frente: "soy daltónico", "tengo baja visión")
porque cualquier modelo decente los saca bien; esos siguen probándose
en test_local.py / la versión larga de este archivo si la conservas.

Usa los IDs enteros reales del seed (id_user=1, id_account=1 — ver
backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs).

Uso (desde la carpeta mcp/, con el venv activo):
    python test_local_accessibility.py
"""

import asyncio
import json
import logging

from dotenv import load_dotenv
from groq import APIStatusError, RateLimitError

load_dotenv()  # carga GROQ_API_KEY del .env ANTES de importar groq_client

from app.ia.accessibility_templates import ACCESSIBILITY_TEMPLATE_IDS
from app.ia.groq_client import GroqPlanner
from app.logging_config import setup_logging

logger = setup_logging(level=logging.INFO)

# Pausa entre casos (segundos) para no saturar el límite de tokens/minuto
# (TPM) del tier gratuito de Groq. Si sigues viendo 429/413, sube este
# valor o corre menos casos por ejecución (parte casos_de_prueba en dos).
PAUSA_ENTRE_CASOS_SEG = 8


# Cada caso trae, además del mensaje/contexto, el template que
# ESPERARÍAMOS que la IA elija (solo referencia visual al imprimir el
# resultado: no se usa para hacer fallar el script, porque el modelo
# puede razonar distinto y seguir siendo una respuesta válida).
#
# Se dejaron fuera a propósito los casos "de libro" (mensaje corto,
# perfecto, nombrando la condición de frente: "soy daltónico", "tengo
# baja visión"...) porque esos ya los cubre test_local_accessibility
# original y casi cualquier modelo los saca bien. Aquí se dejan solo los
# rebuscados: sin nombrar la condición, mezclados con otra intención en
# el mismo mensaje, o escritos como de verdad tiende a escribir un señor
# —sin acentos, con rodeos, quejándose antes de llegar al punto, sin
# signos de puntuación completos—.
casos_de_prueba = [
    # Daltonismo implícito + reclamo mezclado con la intención real
    # (transferir), sin acentos ni puntuación, como se escribe desde el
    # celular con prisa.
    {
        "mensaje": "oiga joven fijese que no le veo bien a los botones verdes y rojos de las transferencias ya me equivoque una vez, de todos modos necesito mandarle 500 pesos a mi hijo",
        "contexto": {"id_account": 1, "id_user": 1},
        "esperado": "algún color_blind_* + intent make_transfer (la condición va escondida en una queja, no anunciada)",
    },
    # Adulto mayor implícito: nunca dice "adulto mayor" ni su edad, se
    # infiere por el tono, las referencias (nieta, lentes) y la queja.
    {
        "mensaje": "Buenas tardes disculpe la molestia, mi nieta me instalo esto pero yo con mis lentes no le distingo bien las letras de hasta arriba, quisiera ver cuanto tengo en mi cuenta",
        "contexto": {"id_account": 1, "id_user": 1},
        "esperado": "senior (nada de 'adulto mayor' ni edad explícita)",
    },
    # Discapacidad motriz disfrazada de queja sobre la app, no sobre la
    # persona ("se traba", "no le doy bien") — fácil de confundir con un
    # simple reporte de bug de UI.
    {
        "mensaje": "esta aplicacion esta rara, uno le quiere dar al boton de transferir y siempre le atino al de al lado, se me resbala el dedo con el temblor que tengo desde el año pasado",
        "contexto": {"id_user": 1},
        "esperado": "motor_impairment (la causa real viene al final, casi como aparte)",
    },
    # Baja alfabetización disfrazada de "no entiendo los términos", sin
    # decir directamente que no sabe leer bien — riesgo de que el modelo
    # lo confunda con "explícame qué es una transferencia" genérico.
    {
        "mensaje": "que es eso de conciliacion que me sale en la pantalla, es que yo no fui mucho a la escuela y esas palabras raras no las entiendo bien",
        "contexto": {"id_account": 1, "id_user": 1},
        "esperado": "low_literacy",
    },
    # Trampa: menciona "no veo bien" pero la causa real es cognitiva
    # (se pierde, se le olvida, se confunde), no visual — para ver si el
    # modelo cae en low_vision por reflejo o lee bien el contexto.
    {
        "mensaje": "no es que no vea la pantalla, es que me pierdo, entro a ver mis movimientos y ya no se ni como regrese ni que estaba buscando, se me hace un lio todo junto",
        "contexto": {"id_account": 1, "id_user": 1},
        "esperado": "cognitive_impairment (trampa: 'me pierdo' no es visión, es carga cognitiva)",
    },
    # Combinado extremo: tres señales encimadas en un solo mensaje largo
    # y desordenado (visión + motriz + queja de letra chica), típico de
    # un mensaje real de voz-a-texto de un adulto mayor.
    {
        "mensaje": "mire yo ya no veo tan bien de un ojo y ademas con la mano derecha se me hace dificil por la artritis y para acabarla la letra de los estados de cuenta esta bien chiquita no se si me pueden ayudar con todo eso junto",
        "contexto": {"id_account": 1, "id_user": 1},
        "esperado": "senior o low_vision (múltiples señales encimadas, sin gerarquía clara)",
    },
]


async def main() -> None:
    planner = GroqPlanner()

    aciertos = 0
    fallidos: list[tuple[int, str, str]] = []  # (num_caso, mensaje, error)

    for i, caso in enumerate(casos_de_prueba, start=1):
        print(f"\n{'=' * 60}")
        print(f"CASO {i}: {caso['mensaje']}")
        print(f"Esperado (referencia): {caso['esperado']}")
        print("=" * 60)

        try:
            plan = await planner.plan(user_message=caso["mensaje"], context=caso["contexto"])
        except RateLimitError as e:
            # 429: se agotó tokens/peticiones por minuto. El cliente ya
            # reintenta con backoff internamente; si llega aquí es que se
            # acabaron los reintentos. Saltamos el caso y seguimos.
            print(f"⚠️  Rate limit (429) agotado para este caso, se salta: {e}")
            fallidos.append((i, caso["mensaje"], "429 rate limit"))
            await asyncio.sleep(PAUSA_ENTRE_CASOS_SEG)
            continue
        except APIStatusError as e:
            # 413 u otro error de la API: normalmente significa que el
            # prompt+schema de ESTE modelo ya excede su cuota de TPM
            # (no se arregla esperando). Se salta el caso, no se aborta
            # el resto del test.
            print(f"⚠️  Error de la API de Groq, se salta este caso: {e}")
            fallidos.append((i, caso["mensaje"], str(e)[:200]))
            await asyncio.sleep(PAUSA_ENTRE_CASOS_SEG)
            continue

        # ActionPlan ya es un modelo Pydantic tipado (schemas.py): esto es
        # exactamente el JSON que consumirá Cain y, más adelante, el
        # traductor a interfaz visual.
        print(json.dumps(plan.model_dump(mode="json"), indent=2, ensure_ascii=False))

        template_elegido = plan.accessibility_template
        es_valido = template_elegido in ACCESSIBILITY_TEMPLATE_IDS
        marca = "✅" if es_valido else "❌ (id fuera del catálogo)"
        print(f"\n>>> accessibility_template elegido: {template_elegido} {marca}")
        if es_valido:
            aciertos += 1

        # Pausa fija entre casos para no acumular tokens/minuto y disparar
        # otro 429/413 en el siguiente caso.
        if i < len(casos_de_prueba):
            await asyncio.sleep(PAUSA_ENTRE_CASOS_SEG)

    print(f"\n{'=' * 60}")
    print(f"Resumen: {aciertos}/{len(casos_de_prueba)} casos con un accessibility_template válido del catálogo")
    if fallidos:
        print(f"Casos saltados por error de API ({len(fallidos)}):")
        for num, mensaje, err in fallidos:
            print(f"  - CASO {num}: {mensaje!r} -> {err}")
        print("Si ves varios '413'/rate limit, corre menos casos por ejecución")
        print("(parte casos_de_prueba en dos listas) o sube PAUSA_ENTRE_CASOS_SEG.")
    print("(Revisa manualmente arriba si el template elegido tiene sentido para cada mensaje;")
    print(" este script no falla el test solo por no coincidir con 'esperado', es una referencia.)")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

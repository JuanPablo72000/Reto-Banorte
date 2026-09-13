"""
Visualizaciones deterministas construidas desde los resultados REALES de los
steps ejecutados (no dependen de que la IA las invente).

Por qué existe: la regla 13 del SYSTEM_INSTRUCTION deja las gráficas al
criterio del modelo, y los modelos chicos a veces no las generan o las
generan con datos inventados/desordenados. Este módulo garantiza que casi
todo turno con datos numéricos traiga 1-4 gráficas correctas, ORDENADAS
(series de tiempo ascendentes por fecha; categorías descendentes por monto)
y con etiquetas de accesibilidad completas.

Cada generador recibe el `result` crudo del step (lista, dict con "muestra"
o modelo único ya serializado por orquestador._resumir) y devuelve dicts con
la forma que espera el frontend (Visualization de action-plan.ts):
    {type, title, data: [{<labelKey>: str, <serieKey>: number, ...}],
     description, accessibility_label}

El orquestador las fusiona con las que la IA sí haya generado (las de la IA
van primero —p. ej. bank_card— y se deduplica por título).
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger("mcp_ia.visualizaciones")

# Vocabulario del ledger (DbSeeder/mock_data) -> nombre legible.
_NOMBRE_CATEGORIA = {
    "nomina": "Nómina",
    "freelance": "Freelance",
    "intereses": "Intereses",
    "cashback": "Cashback",
    "traspaso": "Traspasos",
    "renta": "Renta",
    "suscripcion": "Suscripciones",
    "gym": "Gimnasio",
    "servicios": "Servicios",
    "super": "Supermercado",
    "restaurante": "Restaurantes",
    "comida_rapida": "Comida rápida",
    "transporte": "Transporte",
    "gasolina": "Gasolina",
    "farmacia": "Farmacia",
    "entretenimiento": "Entretenimiento",
    "educacion": "Educación",
    "medico": "Médico",
    "pago_tarjeta": "Pago de tarjetas",
    "transferencia": "Transferencias",
    "otro": "Otros",
}

_ESTADO_CONCILIACION = {
    "matched": "Conciliado",
    "pending": "En revisión",
    "unmatched": "Sin coincidencia",
    "mismatch": "Sin coincidencia",
}

_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

_CLAVES_ETIQUETA = ("name", "label", "categoria", "fecha", "alias")
_MAX_PUNTOS = 31


def _num(v: Any) -> float:
    try:
        if v is None or isinstance(v, bool):
            return 0.0
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _fmt_fecha(v: Any) -> str:
    """'2026-09-05' | '2026-09-05T00:00:00' -> '05/09'."""
    s = str(v or "")[:10]
    partes = s.split("-")
    if len(partes) == 3 and all(p.isdigit() for p in partes):
        return f"{partes[2]}/{partes[1]}"
    return s


def _rango(args: Optional[dict]) -> str:
    """Sufijo de título cuando la consulta trae rango de fechas explícito."""
    if not args:
        return ""
    a, b = args.get("date_from"), args.get("date_to")
    if a and b:
        return f" ({_fmt_fecha(a)} – {_fmt_fecha(b)})"
    if a:
        return f" (desde {_fmt_fecha(a)})"
    if b:
        return f" (hasta {_fmt_fecha(b)})"
    return ""


def _filas(resultado: Any) -> list[dict]:
    """Normaliza el result de un step a una lista de dicts."""
    if resultado is None:
        return []
    if isinstance(resultado, list):
        return [r for r in resultado if isinstance(r, dict)]
    if isinstance(resultado, dict):
        muestra = resultado.get("muestra")
        if isinstance(muestra, list):
            return [r for r in muestra if isinstance(r, dict)]
        return [resultado]
    return []


def _viz(tipo: str, titulo: str, data: list[dict], descripcion: str) -> dict:
    """Arma la visualización + accessibility_label legible (hasta 8 puntos)."""
    if not data:
        return {}
    claves_num = [k for k in data[0] if k not in _CLAVES_ETIQUETA]
    partes = []
    for fila in data[:8]:
        etiqueta = str(fila.get(_etiqueta_de(fila), ""))
        valores = ", ".join(f"{k} {_num(fila.get(k)):.2f}" for k in claves_num)
        partes.append(f"{etiqueta}: {valores}")
    sufijo = f" (y {len(data) - 8} más)" if len(data) > 8 else ""
    nombre_tipo = {"bar": "barras", "line": "líneas", "area": "área", "pie": "pastel", "donut": "dona"}.get(tipo, tipo)
    return {
        "type": tipo,
        "title": titulo,
        "data": data,
        "description": descripcion,
        "accessibility_label": f"Gráfico de {nombre_tipo} «{titulo}». " + "; ".join(partes) + sufijo,
    }


def _etiqueta_de(fila: dict) -> str:
    for k in _CLAVES_ETIQUETA:
        if k in fila:
            return k
    return next(iter(fila), "")


def _recortar(data: list[dict]) -> list[dict]:
    """Series de tiempo: si hay más puntos que _MAX_PUNTOS, agrega por semana
    (promedio) para que la gráfica se lea bien en móvil."""
    return data[:_MAX_PUNTOS]


# ---------------------------------------------------------------------------
# Generadores por tool
# ---------------------------------------------------------------------------
def _daily_balance(filas: list[dict], args: Optional[dict]) -> list[dict]:
    filas = sorted(filas, key=lambda r: str(r.get("date", "")))
    if not filas:
        return []
    rango = _rango(args)
    saldo = [
        {"fecha": _fmt_fecha(r.get("date")), "Saldo": round(_num(r.get("closing_balance")), 2)}
        for r in filas
    ]
    flujos = [
        {"fecha": _fmt_fecha(r.get("date")), "Ingresos": round(_num(r.get("income")), 2), "Gastos": round(_num(r.get("expenses")), 2)}
        for r in filas
        if _num(r.get("income")) > 0 or _num(r.get("expenses")) > 0
    ]
    out = [_viz("area", f"Evolución del saldo{rango}", _recortar(saldo),
                "Saldo al cierre de cada día del periodo consultado.")]
    if len(flujos) > 1:
        out.append(_viz("bar", f"Ingresos vs gastos por día{rango}", _recortar(flujos),
                        "Comparación diaria de entradas y salidas de dinero."))
    return [v for v in out if v]


def _transactions(filas: list[dict], args: Optional[dict]) -> list[dict]:
    if not filas:
        return []
    rango = _rango(args)
    # 1) Dona de gastos por categoría (descendente por monto).
    por_cat: dict[str, float] = {}
    for t in filas:
        if t.get("direction") != "debit" or t.get("status") in ("failed", "reversed"):
            continue
        cat = _NOMBRE_CATEGORIA.get(str(t.get("category", "")), str(t.get("category", "Otros")).title())
        por_cat[cat] = round(por_cat.get(cat, 0.0) + _num(t.get("amount")), 2)
    donut_data = [{"categoria": k, "monto": v} for k, v in sorted(por_cat.items(), key=lambda kv: kv[1], reverse=True)[:8]]
    # 2) Resumen ingresos vs gastos.
    ingresos = round(sum(_num(t.get("amount")) for t in filas if t.get("direction") == "credit" and t.get("status") == "posted"), 2)
    gastos = round(sum(v for v in por_cat.values()), 2)
    resumen = [{"name": "Ingresos", "value": ingresos}, {"name": "Gastos", "value": gastos}]
    # 3) Gasto acumulado por día (ascendente por fecha).
    por_dia: dict[str, float] = {}
    for t in filas:
        if t.get("direction") == "debit" and t.get("status") == "posted":
            d = str(t.get("date", ""))[:10]
            por_dia[d] = round(por_dia.get(d, 0.0) + _num(t.get("amount")), 2)
    acumulado, acum = [], 0.0
    for d in sorted(por_dia):
        acum = round(acum + por_dia[d], 2)
        acumulado.append({"fecha": _fmt_fecha(d), "Gasto acumulado": acum})

    out = []
    if donut_data:
        out.append(_viz("donut", f"Gastos por categoría{rango}", donut_data,
                        "Proporción del gasto por categoría en el periodo."))
    if ingresos or gastos:
        out.append(_viz("bar", f"Ingresos vs gastos{rango}", resumen,
                        "Total de dinero que entró contra el que salió en el periodo."))
    if len(acumulado) > 2:
        out.append(_viz("line", f"Gasto acumulado por día{rango}", _recortar(acumulado),
                        "Cómo se fue acumulando el gasto día con día."))
    return [v for v in out if v]


def _expense_categories(filas: list[dict], args: Optional[dict]) -> list[dict]:
    data = [
        {"categoria": str(r.get("name") or r.get("code")), "monto": round(_num(r.get("total_amount")), 2)}
        for r in filas
        if _num(r.get("total_amount")) > 0
    ]
    data.sort(key=lambda d: d["monto"], reverse=True)
    v = _viz("donut", "Gasto real por categoría", data[:8],
             "Distribución del gasto agregado por categoría.")
    return [v] if v else []


def _accounts(filas: list[dict], args: Optional[dict]) -> list[dict]:
    data = [
        {"alias": str(r.get("alias")), "saldo": round(_num(r.get("balance")), 2)}
        for r in filas
        if r.get("status") == "active" and _num(r.get("balance")) > 0
    ]
    data.sort(key=lambda d: d["saldo"], reverse=True)
    v = _viz("donut", "Distribución de saldos por cuenta", data,
             "Qué parte de tu dinero está en cada cuenta.")
    return [v] if v else []


def _account_summary(resultado: Any, args: Optional[dict]) -> list[dict]:
    if not isinstance(resultado, dict):
        return []
    cuentas = resultado.get("accounts")
    if isinstance(cuentas, list):
        return _accounts([c for c in cuentas if isinstance(c, dict)], args)
    return []


def _budgets(resultado: Any, args: Optional[dict]) -> list[dict]:
    if not isinstance(resultado, dict):
        return []
    presupuestos = [b for b in (resultado.get("budgets") or []) if isinstance(b, dict)]
    if not presupuestos:
        return []
    presupuestos.sort(key=lambda b: _num(b.get("usage_percent")), reverse=True)
    data = [
        {
            "categoria": str(b.get("category_name")),
            "Gastado": round(_num(b.get("current_spent")), 2),
            "Límite": round(_num(b.get("amount_limit")), 2),
        }
        for b in presupuestos[:8]
    ]
    mes = _MESES[int(resultado.get("month", 1)) - 1] if resultado.get("month") else ""
    v = _viz("bar", f"Presupuesto vs gasto{f' — {mes}' if mes else ''}", data,
             "Cuánto has gastado contra el límite de cada categoría (ordenado por uso).")
    return [v] if v else []


def _goals(filas: list[dict], args: Optional[dict]) -> list[dict]:
    data = [
        {"name": str(r.get("name")), "Progreso %": round(_num(r.get("progress_percent")), 1)}
        for r in filas
    ]
    data.sort(key=lambda d: d["Progreso %"], reverse=True)
    v = _viz("bar", "Progreso de metas de ahorro", data[:8],
             "Porcentaje alcanzado de cada meta (ordenado de mayor a menor avance).")
    return [v] if v else []


def _credit_cards(filas: list[dict], args: Optional[dict]) -> list[dict]:
    data = []
    for r in filas:
        limite = _num(r.get("credit_limit"))
        disp = _num(r.get("available_credit"))
        data.append({
            "name": f"{r.get('card_type', 'Tarjeta')} {r.get('card_number_masked', '')}".strip(),
            "Usado": round(max(0.0, limite - disp), 2),
            "Disponible": round(disp, 2),
        })
    v = _viz("bar", "Crédito usado vs disponible", data,
             "Comparación por tarjeta del crédito utilizado contra el disponible.")
    return [v] if v else []


def _transfers(filas: list[dict], args: Optional[dict]) -> list[dict]:
    por_mes: dict[str, float] = {}
    for t in filas:
        if t.get("status") not in ("confirmed",):
            continue
        creada = str(t.get("created_at", ""))[:7]  # yyyy-mm
        if len(creada) == 7 and creada[4] == "-":
            clave = f"{_MESES[int(creada[5:7]) - 1]} {creada[2:4]}"
            por_mes[clave] = round(por_mes.get(clave, 0.0) + _num(t.get("amount")), 2)
    if len(por_mes) < 2:
        return []
    # Orden cronológico (las claves vienen de fechas; reordenar por (año, mes)).
    orden = sorted(por_mes.items(), key=lambda kv: str(kv[0]))
    data = [{"name": k, "Monto": v} for k, v in orden]
    v = _viz("bar", "Transferencias confirmadas por mes", data,
             "Cuánto has transferido (confirmado) en cada mes, en orden cronológico.")
    return [v] if v else []


def _statements(filas: list[dict], args: Optional[dict]) -> list[dict]:
    filas = [s for s in filas if s.get("account_type") != "credito"]
    filas.sort(key=lambda s: str(s.get("period_end", "")))
    data = [
        {
            "name": f"{_fmt_fecha(s.get('period_start'))}–{_fmt_fecha(s.get('period_end'))}",
            "Créditos": round(_num(s.get("total_credits")), 2),
            "Cargos": round(_num(s.get("total_debits")), 2),
        }
        for s in filas[:8]
    ]
    v = _viz("bar", "Créditos vs cargos por periodo", data,
             "Entradas contra salidas de cada estado de cuenta, en orden cronológico.")
    return [v] if v else []


def _reconciliation(filas: list[dict], args: Optional[dict]) -> list[dict]:
    conteo: dict[str, int] = {}
    for r in filas:
        est = _ESTADO_CONCILIACION.get(str(r.get("status")), str(r.get("status")))
        conteo[est] = conteo.get(est, 0) + 1
    data = [{"name": k, "value": v} for k, v in sorted(conteo.items(), key=lambda kv: kv[1], reverse=True)]
    v = _viz("donut", "Conciliación por estado", data,
             "Cuántas conciliaciones están en cada estado.")
    return [v] if v else []


# tool -> generador. Firma: (filas_o_result, args) -> list[dict]
_GENERADORES_POR_FILAS: dict[str, Callable[[list[dict], Optional[dict]], list[dict]]] = {
    "get_daily_balance": _daily_balance,
    "get_transactions": _transactions,
    "get_all_transactions": _transactions,
    "get_expense_categories": _expense_categories,
    "get_accounts": _accounts,
    "get_savings_goals": _goals,
    "get_credit_cards": _credit_cards,
    "get_transfers": _transfers,
    "get_statements": _statements,
    "get_reconciliation_status": _reconciliation,
}

_GENERADORES_POR_RESULTADO: dict[str, Callable[[Any, Optional[dict]], list[dict]]] = {
    "get_account_summary": _account_summary,
    "get_budgets_monthly": _budgets,
}

_MAX_VISUALIZACIONES = 4
_MAX_POR_STEP = 2


def construir_visualizaciones(
    pasos: list[tuple[str, dict, dict]],
    limite: int = _MAX_VISUALIZACIONES,
) -> list[dict]:
    """Recibe [(tool, arguments, salida_ejecutada)] y devuelve hasta
    `limite` visualizaciones deterministas (máx. 2 por step), en el orden
    de los steps. Nunca lanza: cualquier fallo se registra y se ignora."""
    out: list[dict] = []
    titulos: set[str] = set()
    for tool, args, salida in pasos:
        if len(out) >= limite:
            break
        if not isinstance(salida, dict) or not salida.get("ejecutado"):
            continue
        resultado = salida.get("result")
        try:
            generador_resultado = _GENERADORES_POR_RESULTADO.get(tool)
            if generador_resultado is not None:
                nuevas = generador_resultado(resultado, args)
            else:
                generador = _GENERADORES_POR_FILAS.get(tool)
                if generador is None:
                    continue
                nuevas = generador(_filas(resultado), args)
        except Exception:  # noqa: BLE001 — una gráfica rota no tumba el turno
            logger.exception("Fallo generando visualizaciones de %s", tool)
            continue
        for v in nuevas[:_MAX_POR_STEP]:
            if len(out) >= limite or v.get("title") in titulos:
                continue
            titulos.add(v.get("title"))
            out.append(v)
    return out

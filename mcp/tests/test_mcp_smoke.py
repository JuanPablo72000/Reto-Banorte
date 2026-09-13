"""
Smoke test del MCP cableado a la API real — Guillermo + Cain.

Qué prueba (y qué datos arroja):
  Fase A — tools directas (`app.tools.*`, 12 lecturas): imprime los datos
      reales que devuelve cada tool + `x_placeholder` como prueba de
      origen (False = API real, True = mock de respaldo).
  Fase B — protocolo MCP real (`fastmcp.Client` sobre
      `app/server/mcp_server.py`, igual que `mcp_client.py`): lista las
      tools expuestas, llama `get_user_context` + `get_accounts` y corre
      `planificar_accion` ("ver mis movimientos"), imprimiendo intent y
      nº de steps del ActionPlan.
  Fase C — escritura (SOLO con --con-escritura): crea un borrador real de
      $1.00 MXN con `prepare_transfer`, lo confirma con
      `confirm_transfer` y lo relee con `get_transfer_detail`.
      MODIFICA la DB demo de docker (una transferencia pending->confirmed
      más, como la semilla). Sin el flag, esta fase se omite.
  Fase D — contratos: ids inexistentes deben lanzar ValueError.

Uso (desde la carpeta mcp/, con el venv activo):
    python tests/test_mcp_smoke.py                # lectura + MCP, sin tocar la DB
    python tests/test_mcp_smoke.py --con-escritura # + transferencia $1 real

Requiere: API en BANORTE_API_BASE_URL (default http://localhost:8000,
docker) y mcp/.env con DEEPSEEK_API_KEY y/o GEMINI_API_KEY (solo Fase B).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# El test se corre como script (`python tests/test_mcp_smoke.py`): Python
# solo agrega tests/ al sys.path, así que se inserta mcp/ (raíz de `app`).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from fastmcp import Client  # noqa: E402
from pathlib import Path  # noqa: E402

from app import tools  # noqa: E402
from app.logging_config import setup_logging  # noqa: E402

logger = setup_logging(level=logging.INFO)

CON_ESCRITURA = "--con-escritura" in sys.argv
ID_USER_DEMO = 1
ID_ACCOUNT_DEMO = 1
SERVER_SCRIPT = Path(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app", "server", "mcp_server.py",
)


def _plain(x):
    """Convierte el wrapper Root de FastMCP a tipos planos (dict/list).

    FastMCP envuelve cada modelo Pydantic en una clase `Root` dinámica
    SIN model_dump, pero con los campos como atributos directos en
    snake_case (id_user, no idUser)."""
    if isinstance(x, list):
        return [_plain(i) for i in x]
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    d = getattr(x, "__dict__", None)
    if isinstance(d, dict) and d:
        return {k: _plain(v) for k, v in d.items() if not k.startswith("_")}
    return x


def _dato(resultado):
    """Extrae el payload de CallToolResult como dict/list planos."""
    return _plain(resultado.data)

fallos: list[str] = []
filas_resumen: list[tuple] = []


def _origen(obj) -> str:
    """API o mock según x_placeholder (listas: API si ninguna es placeholder)."""
    if isinstance(obj, list):
        if not obj:
            return "API (vacío)"
        return "mock" if any(getattr(o, "x_placeholder", False) for o in obj) else "API"
    return "mock" if getattr(obj, "x_placeholder", False) else "API"


def _resumen(fase: str, tool: str, dato) -> None:
    n = len(dato) if isinstance(dato, list) else 1
    filas_resumen.append((fase, tool, _origen(dato), n))
    logger.info("[%s] %s -> origen=%s filas=%s", fase, tool, _origen(dato), n)


def _ok(nombre: str, cond: bool, detalle: str = "") -> None:
    print(("OK   " if cond else "FALLO") + f" {nombre}" + (f" | {detalle}" if detalle else ""))
    if not cond:
        fallos.append(nombre)


async def fase_a_lecturas() -> None:
    print("\n--- FASE A: tools directas (API real con fallback a mock) ---")
    ctx = await tools.get_user_context(ID_USER_DEMO)
    _resumen("A", "get_user_context", ctx)
    print(f"usuario: {ctx.name} <{ctx.email}> perfil={ctx.accessibility.accessibility_profile.value}")
    _ok("A user real", ctx.x_placeholder is False, f"x_placeholder={ctx.x_placeholder}")

    accs = await tools.get_accounts(ID_USER_DEMO)
    _resumen("A", "get_accounts", accs)
    for a in accs:
        print(f"cuenta: {a.alias} {a.masked_number} saldo={a.balance} {a.currency}")
    _ok("A accounts real", accs and accs[0].x_placeholder is False)

    summ = await tools.get_account_summary(ID_USER_DEMO)
    _resumen("A", "get_account_summary", summ)
    print(f"summary: total={summ.total_balance} {summ.currency} cuentas={len(summ.accounts)}")

    txs = await tools.get_transactions(ID_ACCOUNT_DEMO, limit=5)
    _resumen("A", "get_transactions", txs)
    for t in txs:
        print(f"tx: {t.date} {t.direction} {t.amount} '{t.description}' [{t.category}]")

    alltx = await tools.get_all_transactions(ID_USER_DEMO, limit=5)
    _resumen("A", "get_all_transactions", alltx)
    print(f"all_transactions: {len(alltx)} movimientos")

    bal = await tools.get_daily_balance(ID_ACCOUNT_DEMO)
    _resumen("A", "get_daily_balance", bal)
    for b in bal:
        print(f"balance: {b.date} apertura={b.opening_balance} cierre={b.closing_balance}")

    trs = await tools.get_transfers(id_user=ID_USER_DEMO)
    _resumen("A", "get_transfers", trs)
    for t in trs:
        print(f"transfer: id={t.id_transfer} {t.amount} {t.currency} -> '{t.destination_alias}' [{t.status}]")

    rec = await tools.get_reconciliation_status(id_user=ID_USER_DEMO)
    _resumen("A", "get_reconciliation_status", rec)
    print(f"reconciliation: {len(rec)} matches")

    cats = await tools.get_expense_categories()
    _resumen("A", "get_expense_categories", cats)
    print(f"expense_categories: {len(cats)} ({', '.join(c.code for c in cats[:5])}...)")

    hoy = datetime.now().date()
    bud = await tools.get_budgets_monthly(hoy.year, hoy.month)
    _resumen("A", "get_budgets_monthly", bud)
    print(f"budgets {hoy.year}-{hoy.month:02d}: limite={bud.total_limit} gastado={bud.total_spent} "
          f"categorias={len(bud.budgets)}")

    goals = await tools.get_savings_goals()
    _resumen("A", "get_savings_goals", goals)
    for g in goals:
        print(f"meta: '{g.name}' {g.current_amount}/{g.target_amount} [{g.status}]")

    cards = await tools.get_credit_cards()
    _resumen("A", "get_credit_cards", cards)
    for c in cards:
        print(f"tarjeta: {c.card_number_masked} limite={c.credit_limit} disponible={c.available_credit}")


async def fase_b_protocolo_mcp() -> None:
    print("\n--- FASE B: protocolo MCP real (fastmcp.Client -> mcp_server stdio) ---")
    client = Client(SERVER_SCRIPT)
    async with client:
        exposed = await client.list_tools()
        nombres = sorted(t.name for t in exposed)
        print(f"tools expuestas ({len(nombres)}): {', '.join(nombres)}")
        _ok("B planificar_accion expuesta", "planificar_accion" in nombres)
        _ok("B get_credit_cards expuesta", "get_credit_cards" in nombres)

        r = await client.call_tool("get_user_context", {"id_user": ID_USER_DEMO})
        d = _dato(r)
        print("MCP get_user_context:", json.dumps(d, ensure_ascii=False, default=str)[:200], "...")
        _ok("B MCP user ok",
            isinstance(d, dict) and d.get("id_user") == 1)

        r = await client.call_tool("get_accounts", {"id_user": ID_USER_DEMO})
        d = _dato(r)
        print(f"MCP get_accounts: {len(d)} cuenta(s)")
        _ok("B MCP accounts ok", isinstance(d, list) and len(d) >= 1)

        r = await client.call_tool(
            "planificar_accion",
            {"mensaje_usuario": "Quiero ver mis movimientos del mes pasado",
             "contexto": {"id_user": ID_USER_DEMO, "id_account": ID_ACCOUNT_DEMO}},
        )
        plan = _dato(r)
        print(f"MCP planificar_accion: intent={plan.get('intent')} "
              f"steps={len(plan.get('steps', []))} "
              f"sugerencias={len(plan.get('suggested_actions', []))}")
        _ok("B MCP plan intent", plan.get("intent") == "view_transactions", str(plan.get("intent")))
        _ok("B MCP plan steps", len(plan.get("steps", [])) >= 1)
        filas_resumen.append(("B", "planificar_accion (MCP)", "IA", len(plan.get("steps", []))))


async def fase_c_escritura() -> None:
    print("\n--- FASE C: escritura contra DB demo (requiere --con-escritura) ---")
    if not CON_ESCRITURA:
        print("omitida (pasa --con-escritura para crear una transferencia real de $1)")
        return
    draft = await tools.prepare_transfer(
        ID_USER_DEMO, ID_ACCOUNT_DEMO, "SmokeMCP", 1.0, "MXN", "prueba test_mcp_smoke"
    )
    print(f"draft: id={draft.id_transfer} status={draft.status} "
          f"masked={draft.destination_masked} placeholder={draft.x_placeholder}")
    _ok("C draft real", draft.x_placeholder is False and draft.status in ("pending", "pending_confirmation"))
    filas_resumen.append(("C", "prepare_transfer", _origen(draft), 1))

    conf = await tools.confirm_transfer(draft.id_transfer, "app")
    print(f"confirmada: id={conf.id_transfer} status={conf.status} at={conf.confirmed_at}")
    _ok("C confirmada", conf.status == "confirmed")
    filas_resumen.append(("C", "confirm_transfer", _origen(conf), 1))

    det = await tools.get_transfer_detail(draft.id_transfer)
    print(f"detalle: id={det.id_transfer} status={det.status}")
    _ok("C detalle", det.status == "confirmed")


async def fase_d_contratos() -> None:
    print("\n--- FASE D: contratos de error ---")
    for coro, nombre in [
        (tools.get_user_context(999), "user 999"),
        (tools.get_account_detail(999), "account 999"),
        (tools.get_transfer_detail(999999), "transfer 999999"),
    ]:
        try:
            await coro
            _ok(f"D ValueError {nombre}", False, "no lanzó error")
        except ValueError as exc:
            _ok(f"D ValueError {nombre}", True, str(exc)[:60])


async def main() -> int:
    print("=" * 70)
    print(f"SMOKE MCP | mode={os.getenv('BANORTE_API_MODE', 'auto')} "
          f"| base={os.getenv('BANORTE_API_BASE_URL', 'http://localhost:8000')} "
          f"| escritura={'SI' if CON_ESCRITURA else 'no'}")
    print("=" * 70)
    await fase_a_lecturas()
    await fase_b_protocolo_mcp()
    await fase_c_escritura()
    await fase_d_contratos()

    print("\n" + "=" * 70 + "\nRESUMEN")
    for fase, tool, origen, n in filas_resumen:
        print(f"[{fase}] {tool:28s} origen={origen:12s} filas={n}")
    print("=" * 70)
    print("FALLOS:", fallos if fallos else "ninguno")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

"""
Cliente HTTP real contra BancaAdaptativa.Api — parte de Cain (integración).

Reemplaza, endpoint por endpoint, a placeholders/mock_data.py. Las rutas y
métodos de abajo están copiados directo de
backend/src/BancaAdaptativa.Api/Endpoints/*.cs, así que si Pablo cambia una
ruta ahí, hay que actualizarla aquí también (no hay generación automática
de cliente todavía — contracts/openapi/ está vacío por ahora).

Notas de autenticación:
- La API real usa JWT Bearer (ver Program.cs -> AddJwtBearer). Este cliente
  NO gestiona login de usuario final: recibe un token ya obtenido (por
  ejemplo, el que use el propio backend de sesión, o uno de pruebas vía
  POST /auth/login) y lo manda en el header Authorization.
- Para desarrollo local, `BancaApiClient.login()` permite obtener un token
  usando el usuario semilla (demo@banorte.mx / Demo123!, ver DbSeeder.cs).

Notas de configuración:
- El contrato A2UI-MCP (contracts/a2ui/a2ui-mcp-contract.yaml) y docker
  (docker-compose.yml) exponen la API en "http://localhost:8000". El puerto
  "http://localhost:5178" solo aplica al backend .NET corriendo local sin
  docker (Properties/launchSettings.json). Se deja configurable por
  variable de entorno (BANORTE_API_BASE_URL) para no depender de cuál
  esté vigente cuando esto se lea.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime
from typing import Optional

import httpx

logger = logging.getLogger("mcp_ia.api_client")

DEFAULT_BASE_URL = os.getenv("BANORTE_API_BASE_URL", "http://localhost:8000")
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("BANORTE_API_TIMEOUT", "10"))


class BancaApiError(RuntimeError):
    """Error de negocio devuelto por la API (4xx/5xx ya interpretado)."""

    def __init__(self, status_code: int, detail: object):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"BancaAdaptativa.Api respondió {status_code}: {detail!r}")


class BancaApiClient:
    """Cliente delgado sobre httpx.AsyncClient. Un objeto por request/sesión
    de usuario (guarda el token de ESE usuario, no es un singleton global)."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, token: Optional[str] = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=DEFAULT_TIMEOUT_SECONDS) as client:
            response = await client.request(method, path, headers=self._headers(), **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            logger.warning("BancaAdaptativa.Api %s %s -> %s: %r", method, path, response.status_code, detail)
            raise BancaApiError(response.status_code, detail)
        return response

    # -- Auth --------------------------------------------------------------
    async def login(self, email: str, password: str) -> dict:
        """POST /auth/login -> AuthResponse (Token, ExpiresAtUtc, User)."""
        resp = await self._request("POST", "/auth/login", json={"email": email, "password": password})
        data = resp.json()
        self._token = data.get("token")
        return data

    async def register(self, name: str, email: str, password: str, locale: str = "es-MX") -> dict:
        """POST /auth/register -> UserDto (201 Created)."""
        resp = await self._request(
            "POST", "/auth/register",
            json={"name": name, "email": email, "password": password, "locale": locale},
        )
        return resp.json()

    # -- Sistema -------------------------------------------------------------
    async def get_server_time(self) -> dict:
        """GET /server-time -> ServerTimeResponse. No requiere auth."""
        resp = await self._request("GET", "/server-time")
        return resp.json()

    # -- Usuario / preferencias (GET /users/me + GET/PUT /me/preferences) ---
    async def get_user_me(self) -> dict:
        """GET /users/me -> UserDto."""
        resp = await self._request("GET", "/users/me")
        return resp.json()

    async def get_me_preferences(self) -> dict:
        """GET /me/preferences -> AccessibilityPreferenceResponse."""
        resp = await self._request("GET", "/me/preferences/")
        return resp.json()

    async def update_me_preferences(self, cambios: dict) -> dict:
        """PUT /me/preferences -> AccessibilityPreferenceResponse actualizado."""
        resp = await self._request("PUT", "/me/preferences/", json=cambios)
        return resp.json()

    # -- Cuentas (AccountEndpoints.cs) --------------------------------------
    async def get_accounts(
        self,
        status: Optional[str] = None,
        account_type: Optional[str] = None,
    ) -> list[dict]:
        """GET /accounts?status=&accountType= -> list[AccountResponse]."""
        params = {"status": status, "accountType": account_type}
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", "/accounts", params=params)
        return resp.json()

    async def get_account_summary(self) -> dict:
        """GET /me/account-summary -> AccountSummaryResponse."""
        resp = await self._request("GET", "/me/account-summary")
        return resp.json()

    async def get_account(self, id_account: int) -> dict:
        """GET /accounts/{accountId} -> AccountResponse."""
        resp = await self._request("GET", f"/accounts/{id_account}")
        return resp.json()

    async def get_account_transactions(
        self,
        id_account: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category: Optional[str] = None,
        expense_category: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """GET /accounts/{accountId}/transactions -> list[TransactionResponse]."""
        params = {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
            "category": category,
            "expenseCategory": expense_category,
            "direction": direction,
            "status": status,
            "search": search,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", f"/accounts/{id_account}/transactions", params=params)
        return resp.json()

    async def get_all_transactions(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        category: Optional[str] = None,
        expense_category: Optional[str] = None,
        direction: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        id_account: Optional[int] = None,
    ) -> list[dict]:
        """GET /me/transactions -> list[TransactionResponse] (transversal)."""
        params = {
            "accountId": id_account,
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
            "category": category,
            "expenseCategory": expense_category,
            "direction": direction,
            "status": status,
            "search": search,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", "/me/transactions", params=params)
        return resp.json()

    async def get_account_daily_balances(
        self,
        id_account: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[dict]:
        """GET /accounts/{accountId}/daily-balances -> list[DailyBalanceResponse]."""
        params = {
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
        }
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", f"/accounts/{id_account}/daily-balances", params=params)
        return resp.json()

    async def get_reconciliation(self, status: Optional[str] = None) -> list[dict]:
        """GET /reconciliation?status= -> list[ReconciliationResponse]."""
        params = {"status": status} if status is not None else {}
        resp = await self._request("GET", "/reconciliation", params=params)
        return resp.json()

    # -- Estados de cuenta y categorías (AccountEndpoints.cs) ---------------
    async def get_statements(
        self,
        id_account: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """GET /accounts/{accountId}/statements -> list[StatementResponse]."""
        params = {"year": year, "month": month, "status": status}
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", f"/accounts/{id_account}/statements", params=params)
        return resp.json()

    async def get_statement_detail(self, id_account: int, id_statement: int) -> dict:
        """GET /accounts/{accountId}/statements/{statementId} -> StatementDetailResponse."""
        resp = await self._request("GET", f"/accounts/{id_account}/statements/{id_statement}")
        return resp.json()

    async def get_expense_categories(self, search: Optional[str] = None) -> list[dict]:
        """GET /expense-categories?search= -> list[ExpenseCategoryResponse]."""
        params = {"search": search} if search is not None else {}
        resp = await self._request("GET", "/expense-categories", params=params)
        return resp.json()

    # -- Transferencias (TransferEndpoints.cs) ------------------------------
    async def create_transfer(
        self,
        id_origin_account: int,
        destination_alias: str,
        destination_masked: str,
        amount: float,
        currency: str = "MXN",
        concept: str = "",
        idempotency_key: Optional[str] = None,
    ) -> dict:
        """POST /transfers -> TransferResponse (201 Created)."""
        payload = {
            "idOriginAccount": id_origin_account,
            "destinationAlias": destination_alias,
            "destinationMasked": destination_masked,
            "amount": amount,
            "currency": currency,
            "concept": concept,
        }
        if idempotency_key:
            payload["idempotencyKey"] = idempotency_key
        resp = await self._request("POST", "/transfers/", json=payload)
        return resp.json()

    async def get_transfer(self, id_transfer: int) -> dict:
        """GET /transfers/{transferId} -> TransferResponse."""
        resp = await self._request("GET", f"/transfers/{id_transfer}")
        return resp.json()

    async def get_transfers(
        self,
        status: Optional[str] = None,
        id_origin_account: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50,
    ) -> list[dict]:
        """GET /transfers -> list[TransferResponse]."""
        params = {
            "status": status,
            "originAccountId": id_origin_account,
            "from": date_from.isoformat() if date_from else None,
            "to": date_to.isoformat() if date_to else None,
            "limit": limit,
        }
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", "/transfers", params=params)
        return resp.json()

    async def confirm_transfer(self, id_transfer: int, method: str = "app") -> dict:
        """POST /transfers/{transferId}/confirm -> {"transfer": ..., "confirmation": ...}."""
        resp = await self._request("POST", f"/transfers/{id_transfer}/confirm", json={"method": method})
        return resp.json()

    # -- Presupuestos (BudgetEndpoints.cs) ----------------------------------
    async def get_budgets_monthly(
        self,
        year: int,
        month: int,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """GET /me/budgets/monthly -> BudgetMonthlySummaryResponse."""
        params = {"year": year, "month": month, "category": category, "status": status}
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request("GET", "/me/budgets/monthly", params=params)
        return resp.json()

    # -- Metas de ahorro (SavingsGoalEndpoints.cs) --------------------------
    async def get_savings_goals(self, status: Optional[str] = None) -> list[dict]:
        """GET /me/savings-goals/ -> list[SavingsGoalResponse]."""
        params = {"status": status} if status is not None else {}
        resp = await self._request("GET", "/me/savings-goals/", params=params)
        return resp.json()

    # -- Tarjetas de crédito (CreditCardEndpoints.cs) -----------------------
    async def get_credit_cards(self, status: Optional[str] = None) -> list[dict]:
        """GET /me/credit-cards -> list[CreditCardResponse]."""
        params = {"status": status} if status is not None else {}
        resp = await self._request("GET", "/me/credit-cards", params=params)
        return resp.json()

    async def get_credit_card_statements(
        self,
        id_credit_card: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[dict]:
        """GET /me/credit-cards/{cardId}/statements -> list[CreditCardStatementResponse]."""
        params = {"year": year, "month": month}
        params = {k: v for k, v in params.items() if v is not None}
        resp = await self._request(
            "GET", f"/me/credit-cards/{id_credit_card}/statements", params=params
        )
        return resp.json()

    # -- Aún sin endpoint real en BancaAdaptativa.Api -----------------------
    # No existe /memory/query ni /audit/me en Endpoints/*.cs todavía.
    # Cain: en cuanto Pablo los agregue, se implementan aquí igual que los
    # de arriba y placeholders/mock_data.py deja de usarse para esa tool.

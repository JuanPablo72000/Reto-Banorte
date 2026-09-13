"""
Conexión con la API real — parte de Cain (integración).

Este módulo es el puente entre tools/tools.py y
integration/api_client.py:

- `get_authenticated_client()`: devuelve un BancaApiClient con JWT
  vigente (hace login con el usuario demo la primera vez y renueva el
  token cuando expira o cuando la API responde 401).
- `call_api(fn)`: ejecuta `fn(client)`; si la API responde 401, re-hace
  login una vez y reintenta. Traduce errores de red a BancaApiError para
  que tools.py tenga un solo tipo que capturar.
- `API_MODE`: controla si las tools usan la API real, los mocks, o la
  API con fallback a mock ("auto", el default):
    - "api":  solo API real; si falla, se propaga el error.
    - "mock": solo placeholders/mock_data.py (comportamiento anterior).
    - "auto":  intenta la API real y, ante CUALQUIER fallo (red, 4xx/5xx,
      validación), registra un warning y usa el mock. Así la demo nunca
      se cae aunque el backend esté apagado.

Variables de entorno (ver mcp/.env.example):
- BANORTE_API_BASE_URL (default http://localhost:8000, docker)
- BANORTE_API_EMAIL (default demo@banorte.mx, usuario semilla)
- BANORTE_API_PASSWORD (default Demo123!, ver DbSeeder.cs)
- BANORTE_API_TOKEN (opcional, por turno): JWT del usuario final que
  pone el puente del frontend (run_turn.py). Si está presente, se usa
  directo sin login demo; si no, auto-login demo.
- BANORTE_API_MODE (auto|api|mock, default auto)

NOTA: el login automático solo sirve para el usuario semilla. Si a
futuro hay login de usuario final, el token debe venir de la sesión
(no de este módulo) y pasarse directo a BancaApiClient.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional, TypeVar

import httpx

from app.integration.api_client import BancaApiClient, BancaApiError

logger = logging.getLogger("mcp_ia.api_connection")

BASE_URL = os.getenv("BANORTE_API_BASE_URL", "http://localhost:8000")
API_EMAIL = os.getenv("BANORTE_API_EMAIL", "demo@banorte.mx")
API_PASSWORD = os.getenv("BANORTE_API_PASSWORD", "Demo123!")
API_MODE = os.getenv("BANORTE_API_MODE", "auto").strip().lower()
if API_MODE not in ("auto", "api", "mock"):
    logger.warning("BANORTE_API_MODE=%r inválido, usando 'auto'", API_MODE)
    API_MODE = "auto"

T = TypeVar("T")

_client: Optional[BancaApiClient] = None
_token_expires_at: Optional[datetime] = None
_ultimo_demo_token: Optional[str] = None
_login_lock = asyncio.Lock()


def api_mode() -> str:
    """Modo actual: 'auto' | 'api' | 'mock'."""
    return API_MODE


def _token_vigente() -> bool:
    if _client is None or _client._token is None:
        return False
    if _token_expires_at is None:
        return True
    return datetime.now(timezone.utc) < _token_expires_at


def _guardar_expiracion(login_data: dict) -> None:
    global _token_expires_at
    _token_expires_at = None
    raw = login_data.get("expiresAtUtc") or login_data.get("expires_at_utc")
    if raw:
        try:
            exp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            _token_expires_at = exp
        except ValueError:
            logger.warning("No se pudo parsear expiresAtUtc=%r, se reintentará login ante 401", raw)


async def _login(client: BancaApiClient) -> None:
    global _ultimo_demo_token
    data = await client.login(API_EMAIL, API_PASSWORD)
    _guardar_expiracion(data)
    _ultimo_demo_token = client._token
    logger.info("Login a BancaAdaptativa.Api OK (usuario=%s)", API_EMAIL)


async def get_authenticated_client() -> BancaApiClient:
    """Devuelve el cliente compartido con JWT vigente.

    Si hay BANORTE_API_TOKEN en el entorno (lo pone el puente del
    frontend por turno con el JWT del usuario final, ver run_turn.py),
    se usa ese token directo sin login demo. Si no, login automático
    con el usuario semilla (demo) y renovación por expiración/401.
    """
    global _client, _token_expires_at
    token_externo = os.getenv("BANORTE_API_TOKEN", "").strip()
    async with _login_lock:
        if token_externo:
            if _client is None or _client._token != token_externo:
                _client = BancaApiClient(base_url=BASE_URL, token=token_externo)
                _token_expires_at = None
                logger.info("Usando BANORTE_API_TOKEN externo (sesión de usuario final)")
            return _client
        # Sin token externo: sesión demo (resetea si quedó uno externo).
        if _client is None or not _client._token or _client._token != _ultimo_demo_token:
            _client = BancaApiClient(base_url=BASE_URL)
        if not _token_vigente():
            await _login(_client)
        return _client


async def call_api(fn: Callable[[BancaApiClient], Awaitable[T]]) -> T:
    """Ejecuta `fn` contra la API real con re-login ante 401.

    Traduce errores de red (httpx) a BancaApiError para que tools.py
    capture un solo tipo de excepción.
    """
    client = await get_authenticated_client()
    try:
        return await fn(client)
    except BancaApiError as exc:
        if exc.status_code != 401:
            raise
        logger.warning("API respondió 401, renovando token y reintentando una vez")
        async with _login_lock:
            await _login(client)
        return await fn(client)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
        raise BancaApiError(0, f"sin conexión con {BASE_URL}: {exc}") from exc

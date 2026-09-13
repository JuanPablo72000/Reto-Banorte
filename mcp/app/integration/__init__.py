"""Paquete `integration`: cliente HTTP real contra BancaAdaptativa.Api
(backend/src/BancaAdaptativa.Api), parte de Cain.
"""

from .api_client import BancaApiClient, BancaApiError  # noqa: F401
from .connection import api_mode, call_api, get_authenticated_client  # noqa: F401

__all__ = ["BancaApiClient", "BancaApiError", "api_mode", "call_api", "get_authenticated_client"]

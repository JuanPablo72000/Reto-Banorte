"""Paquete `schemas`: modelos Pydantic compartidos, alineados con los DTOs
reales de backend/src/BancaAdaptativa.Api/Dtos/**.

Se re-exporta todo desde `schemas.schemas` para poder seguir escribiendo
`from app.schemas import Account, Transfer, ActionPlan` como antes.
"""

from .schemas import *  # noqa: F401,F403

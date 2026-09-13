"""Paquete `placeholders`: mocks alineados 1:1 al seed real de Pablo
(Data/DbSeeder.cs) mientras Cain conecta integration/api_client.py.
"""

from . import mock_data  # noqa: F401
from .mock_data import find_placeholders  # noqa: F401

__all__ = ["mock_data", "find_placeholders"]

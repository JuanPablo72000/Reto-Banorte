"""
Configuración centralizada de logging para el servidor MCP.

Por qué así:
- El transporte "stdio" de MCP usa stdout para los mensajes JSON-RPC.
  Si algo (un logger, un print, una librería de terceros) escribe en stdout,
  se corrompe el protocolo y el cliente MCP deja de entender las respuestas.
- FastMCP ya configura el logger raíz para que apunte a stderr, pero conviene
  fijarlo explícitamente aquí para no depender de ese comportamiento implícito
  y para poder controlar el formato/nivel en un solo lugar.
- Nunca uses print() en este proyecto: usa siempre logger.info/debug/error.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura el logger raíz para escribir solo en stderr y devuelve
    un logger listo para usar en el módulo que llame a esta función."""

    root = logging.getLogger()
    root.setLevel(level)

    # Evita handlers duplicados si setup_logging se llama más de una vez
    # (por ejemplo, en tests o al recargar el módulo).
    root.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

    return logging.getLogger("mcp_ia")

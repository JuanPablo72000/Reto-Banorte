# Tools MCP conectadas con la API real

## Resumen

`app/tools/tools.py` contiene las funciones de datos expuestas por el servidor MCP. Las firmas públicas se mantienen compatibles con el contrato A2UI y los modelos Pydantic existentes.

La implementación ahora utiliza `BancaApiClient` para comunicarse con `BancaAdaptativa.Api`.

## Cambios principales

- Se reemplazaron los mocks por llamadas HTTP reales.
- Las respuestas de la API se validan mediante modelos Pydantic.
- Se reutiliza un único cliente autenticado por proceso.
- Se mantienen las firmas de las ocho tools originales.
- `search_memory_context` continúa utilizando mock porque `/memory/query` todavía no existe en la API.
- `planificar_accion` continúa delegando la generación de planes al `GroqPlanner`.

## Autenticación

El cliente se crea de forma perezosa mediante `_get_client()`.

```python
_client: Optional[BancaApiClient] = None
```

La primera llamada:

1. Crea una instancia de `BancaApiClient`.
2. Obtiene las credenciales desde:
   - `BANORTE_DEMO_EMAIL`
   - `BANORTE_DEMO_PASSWORD`
3. Usa como valores predeterminados:
   - `demo@banorte.mx`
   - `Demo123!`
4. Ejecuta `POST /auth/login`.
5. Reutiliza el token para las siguientes llamadas.

Actualmente existe un único cliente autenticado por proceso. El parámetro `id_user` se conserva por compatibilidad y logging, pero todavía no selecciona dinámicamente el usuario autenticado.

## Tools disponibles

### `get_user_context`

Obtiene el perfil del usuario y sus preferencias de accesibilidad.

**Endpoints utilizados:**

```text
GET /users/me
GET /me/preferences
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id_user` | `int` | Identificador lógico del usuario. Actualmente solo se utiliza para logging. |

**Retorno:**

```python
UserContext
```

El resultado combina la información de usuario con sus preferencias de accesibilidad.

### `get_accounts`

Obtiene las cuentas del usuario autenticado.

**Endpoint utilizado:**

```text
GET /accounts
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id_user` | `int` | Identificador lógico del usuario. Actualmente solo se utiliza para logging. |

**Retorno:**

```python
list[Account]
```

Cada elemento se valida mediante `Account.model_validate()`.

### `get_transactions`

Obtiene los movimientos de una cuenta, con filtros opcionales por fecha.

**Endpoint utilizado:**

```text
GET /accounts/{accountId}/transactions
```

**Parámetros:**

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---:|---|
| `id_account` | `int` | Obligatorio | Identificador de la cuenta. |
| `date_from` | `date \| None` | `None` | Fecha inicial del rango. |
| `date_to` | `date \| None` | `None` | Fecha final del rango. |
| `limit` | `int` | `20` | Número máximo de movimientos. |

**Retorno:**

```python
list[Transaction]
```

Las fechas se convierten a formato ISO antes de enviarse a la API.

### `get_daily_balance`

Obtiene los balances diarios de una cuenta.

**Endpoint utilizado:**

```text
GET /accounts/{accountId}/daily-balances
```

**Parámetros:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `id_account` | `int` | Identificador de la cuenta. |
| `date_from` | `date \| None` | Fecha inicial opcional. |
| `date_to` | `date \| None` | Fecha final opcional. |

**Retorno:**

```python
list[DailyBalance]
```

### `search_memory_context`

Busca contexto previamente almacenado en la memoria de sesión.

**Estado actual:**

Esta tool todavía utiliza:

```python
mock_data.mock_search_memory_context(...)
```

El endpoint real aún no está disponible:

```text
POST /memory/query
```

**Parámetros:**

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---:|---|
| `id_user` | `int` | Obligatorio | Usuario asociado a la memoria. |
| `query` | `str` | Obligatorio | Texto de búsqueda. |
| `id_session` | `int \| None` | `None` | Sesión opcional. |
| `limit` | `int` | `10` | Número máximo de resultados. |

**Retorno:**

```python
list[dict]
```

No debe utilizarse para devolver datos sensibles completos.

### `prepare_transfer`

Crea un borrador de transferencia. Esta operación todavía no confirma el movimiento.

**Endpoint utilizado:**

```text
POST /transfers
```

**Parámetros:**

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---:|---|
| `id_user` | `int` | Obligatorio | Usuario que solicita la operación. |
| `id_origin_account` | `int` | Obligatorio | Cuenta origen. |
| `destination_alias` | `str` | Obligatorio | Alias del destinatario. |
| `amount` | `float` | Obligatorio | Monto de la transferencia. Debe ser mayor que cero. |
| `currency` | `str` | `"MXN"` | Moneda de la operación. |
| `concept` | `str` | `""` | Concepto de la transferencia. |

**Validaciones:**

```python
if amount <= 0:
    raise ValueError(...)
```

**Retorno:**

```python
Transfer
```

La tool envía actualmente `destination_masked=""` porque ese dato no forma parte de su firma pública.

La transferencia debe confirmarse posteriormente mediante `confirm_transfer`.

### `confirm_transfer`

Confirma una transferencia creada previamente.

**Endpoint utilizado:**

```text
POST /transfers/{transferId}/confirm
```

**Parámetros:**

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---:|---|
| `id_transfer` | `int` | Obligatorio | Identificador de la transferencia. |
| `method` | `str` | `"app"` | Método de confirmación. |

La API devuelve un objeto compuesto:

```json
{
  "transfer": {},
  "confirmation": {}
}
```

La tool extrae únicamente la propiedad `transfer` y la valida como:

```python
Transfer
```

### `get_reconciliation_status`

Obtiene el estado de conciliación entre transferencias y movimientos.

**Endpoint utilizado:**

```text
GET /reconciliation
```

**Parámetros:**

| Parámetro | Tipo | Predeterminado | Descripción |
|---|---|---:|---|
| `id_user` | `int \| None` | `None` | Se conserva por compatibilidad, pero actualmente se ignora. |
| `id_transfer` | `int \| None` | `None` | Filtra localmente por transferencia. |
| `id_account` | `int \| None` | `None` | Actualmente se ignora porque la API no admite este filtro. |

La API devuelve la lista completa y la tool aplica localmente el filtro `id_transfer`, cuando está presente.

**Retorno:**

```python
list[ReconciliationMatch]
```

### `planificar_accion`

Genera un plan de acción mediante IA a partir de un mensaje en lenguaje natural.

**Parámetros:**

| Parámetro | Tipo | Descripción |
|---|---|---|
| `mensaje_usuario` | `str` | Solicitud del usuario. |
| `contexto` | `dict \| None` | Datos conocidos de la sesión, como `id_user` o `id_account`. |

**Ejemplo:**

```python
await planificar_accion(
    "Quiero ver mis movimientos del mes",
    {"id_user": 1, "id_account": 1}
)
```

**Retorno:**

```python
ActionPlan
```

El plan incluye:

- Intención detectada.
- Tools recomendadas.
- Argumentos para cada tool.
- Motivo de cada paso.
- Indicador de confirmación.
- `ui_hint` para la interfaz.
- Respuesta para el usuario.

## Validación de respuestas

Las respuestas JSON de la API se convierten en modelos Pydantic:

```python
Account.model_validate(item)
Transaction.model_validate(item)
Transfer.model_validate(raw_transfer)
```

Esto permite detectar respuestas incompatibles con los contratos esperados antes de entregarlas al servidor MCP.

## Manejo de errores

Los errores HTTP son procesados por `BancaApiClient`.

Las respuestas con código `4xx` o `5xx` generan un `BancaApiError`.

Además, `prepare_transfer` genera `ValueError` cuando el monto es menor o igual a cero.

## Dependencias de configuración

Las tools dependen de las siguientes variables de entorno:

```env
BANORTE_API_BASE_URL=http://localhost:8000
BANORTE_API_TIMEOUT=10
BANORTE_DEMO_EMAIL=demo@banorte.mx
BANORTE_DEMO_PASSWORD=Demo123!
```

Si `BANORTE_API_BASE_URL` no está definida, el cliente utiliza:

```text
http://localhost:5178
```

## Limitaciones actuales

- La autenticación es compartida por proceso.
- No existe todavía autenticación independiente por usuario.
- `id_user` no cambia el usuario autenticado.
- `search_memory_context` continúa usando datos mock.
- `destination_masked` se envía vacío al crear transferencias.
- `get_reconciliation_status` solo filtra localmente por `id_transfer`.
- La API debe estar disponible antes de invocar las tools conectadas.

## Flujo general

```text
Servidor MCP
    |
    v
app/tools/tools.py
    |
    v
_get_client()
    |
    v
BancaApiClient
    |
    v
BancaAdaptativa.Api
    |
    v
Validación Pydantic
    |
    v
Respuesta MCP tipada
```

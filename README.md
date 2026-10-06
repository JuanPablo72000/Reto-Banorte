# Banca Personal Adaptativa

Banca Personal Adaptativa es una aplicación bancaria de demostración que permite consultar información financiera mediante una interfaz web y un asistente en lenguaje natural. El asistente puede mostrar saldos, movimientos, presupuestos, tarjetas y metas de ahorro como texto, tablas y gráficas.

El proyecto incluye:

- Un frontend en Next.js 16.
- Una API REST en .NET 10 con autenticación JWT y SQLite.
- Un servidor MCP en Python que conecta la aplicación con DeepSeek o Gemini.
- Datos demo creados automáticamente al iniciar la API.

## Inicio rápido con Docker Compose

### Requisitos

- Docker Desktop o Docker Engine con Docker Compose.
- Una clave de DeepSeek o Gemini para usar el chat con IA.

### Configuración

1. Crea el archivo de variables de entorno desde el ejemplo:

   ```powershell
   Copy-Item .env.example .env
   ```

   En macOS o Linux:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env`:

   - Cambia `JWT_KEY` por un secreto de al menos 32 caracteres.
   - Define `DEEPSEEK_API_KEY` o `GEMINI_API_KEY`. No es necesario configurar ambas.
   - Conserva las URLs locales si ejecutarás toda la aplicación con Docker Compose.

3. Construye las imágenes e inicia los servicios:

   ```bash
   docker compose up --build -d
   ```

4. Comprueba el estado:

   ```bash
   docker compose ps
   docker compose logs -f
   ```

5. Abre `http://localhost:3000` e inicia sesión con:

   ```text
   Usuario: demo@banorte.mx
   Contraseña: Demo123!
   ```

### Servicios disponibles

| Servicio | URL | Descripción |
|---|---|---|
| Frontend | `http://localhost:3000` | Aplicación web y chat |
| API | `http://localhost:8000` | API REST; salud en `/health` y Swagger en `/swagger` |
| MCP | `http://localhost:8080` | Servidor de herramientas e IA |

### Comandos útiles

```bash
# Detener los contenedores sin borrar la base de datos
docker compose down

# Reconstruir después de cambiar código o variables
docker compose up --build --force-recreate -d

# Ver los logs de un servicio
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f mcp

# Borrar los contenedores y la base SQLite para regenerar los datos demo
docker compose down -v
```

Para iniciar solamente un componente con sus dependencias, indica su nombre:

```bash
docker compose up --build api
docker compose up --build mcp
docker compose up --build frontend
```

También puedes usar el lanzador de Windows, que inicia todo y comprueba que los servicios respondan:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo.ps1
```

## Ejecutar servicios en local

Docker Compose es la forma recomendada porque configura la red y las dependencias automáticamente. Para desarrollo, cada servicio también puede ejecutarse por separado.

### API .NET

Requiere .NET SDK 10. Desde la raíz del repositorio:

```powershell
$env:JWT_KEY="secreto-local-de-al-menos-32-caracteres"
dotnet run --project backend/src/BancaAdaptativa.Api --launch-profile http
```

La API quedará en `http://localhost:5178`. Las migraciones y los datos demo se aplican automáticamente.

### Servidor MCP

Requiere Python 3.12 o superior. Copia `mcp/.env.example` como `mcp/.env`, agrega una clave de IA y usa `BANORTE_API_BASE_URL=http://localhost:5178` si la API también corre localmente.

```powershell
cd mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.server.mcp_server --http
```

En macOS o Linux, activa el entorno con `source .venv/bin/activate`.

### Frontend Next.js

Requiere Node.js 22 y el entorno de Python del MCP. Crea `frontend/.env.local` con:

```dotenv
NEXT_PUBLIC_API_URL=http://localhost:5178
BANORTE_API_BASE_URL=http://localhost:5178
DEEPSEEK_API_KEY=
GEMINI_API_KEY=
```

Define una de las claves de IA y luego ejecuta:

```bash
cd frontend
npm ci
npm run dev
```

El frontend estará disponible en `http://localhost:3000`. Su ruta de chat inicia el puente MCP desde la carpeta `mcp`, por lo que las dependencias de Python deben estar instaladas y el comando `python` debe estar disponible.

## Variables principales

| Variable | Uso |
|---|---|
| `JWT_KEY` | Firma de tokens del backend; mínimo 32 caracteres |
| `NEXT_PUBLIC_API_URL` | URL de la API accesible desde el navegador |
| `BANORTE_API_BASE_URL` | URL de la API usada por el MCP |
| `DEEPSEEK_API_KEY` | Clave opcional del proveedor principal |
| `GEMINI_API_KEY` | Clave opcional del proveedor alternativo |
| `BANORTE_API_MODE` | `auto`, `api` o `mock` |

Las URLs deben incluir el protocolo. Por ejemplo: `https://api-production-4662.up.railway.app`.

## Estructura del repositorio

```text
backend/     API .NET, SQLite, migraciones y pruebas
frontend/    Aplicación Next.js
mcp/         Servidor MCP, orquestador y clientes de IA
contracts/   Contrato A2UI
docs/        Documentación técnica adicional
scripts/     Scripts de arranque y verificación
```

Para información específica de cada componente consulta [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md) y [mcp/README.md](mcp/README.md).

## Consideraciones de seguridad

- No confirmes `.env` ni claves reales en Git.
- Usa un `JWT_KEY` distinto y aleatorio en cada entorno desplegado.
- Las credenciales demo son solamente para desarrollo y demostraciones.
- Usa HTTPS para cualquier API publicada.

Proyecto académico para Reto Banorte.

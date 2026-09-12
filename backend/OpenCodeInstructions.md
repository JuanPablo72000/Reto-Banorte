# OPENCODE_INSTRUCTIONS.md

## Objetivo

Automatizar la implementación y/o corrección del backend de la API del proyecto **Banca Personal Adaptativa** usando:

- .NET 10
- ASP.NET Core Minimal API
- Entity Framework Core
- SQLite
- Swagger/OpenAPI
- Migraciones
- Datos semilla sintéticos
- Manejo de fechas/horas en UTC

La base de datos debe seguir el diagrama E-R del archivo `diagrama-er-banca-personal.md`.

---

## Contexto del proyecto

El proyecto tiene estos módulos:

- Banca personal:
  - Usuarios.
  - Preferencias de accesibilidad.
  - Cuentas.
  - Movimientos.
  - Balance diario.
  - Sesiones.
  - Eventos de memoria.
  - Preferencias detectadas.

- Pagos:
  - Transferencias.
  - Confirmaciones de transferencia.
  - Conciliación.
  - Auditoría.

La API será consumida por:

- Frontend Next.js.
- Servidor MCP.
- Capa de integración.

Por lo tanto, la API debe devolver JSON claro, estable y consistente.

---

## Alcance del trabajo

OpenCode debe trabajar principalmente dentro de:

```text
backend/
```

Especialmente en:

```text
backend/src/BancaAdaptativa.Api/
```

No debe romper la solución existente si ya fue inicializada.

Si ya existen archivos como:

```text
Program.cs
Data/AppDbContext.cs
Models/Entities.cs
Data/DbSeeder.cs
```

Debe:

1. Auditarlos.
2. Corregirlos.
3. Completarlos.
4. Mantener consistencia con las reglas de este documento.

---

## Stack esperado

Backend:

```text
.NET 10
ASP.NET Core Minimal API
Entity Framework Core
SQLite
Swashbuckle / Swagger
```

Paquetes necesarios:

```text
Microsoft.EntityFrameworkCore.Sqlite
Microsoft.EntityFrameworkCore.Design
```

Opcionales si OpenCode los considera necesarios:

```text
EFCore.NamingConventions
```

---

## Estructura esperada del backend

La estructura mínima esperada es:

```text
backend/
├── BancaAdaptativa.sln
├── data/
├── src/
│   └── BancaAdaptativa.Api/
│       ├── Data/
│       │   ├── AppDbContext.cs
│       │   ├── DbSeeder.cs
│       │   └── Migrations/
│       ├── Dtos/
│       ├── Endpoints/
│       ├── Models/
│       │   └── Entities.cs
│       ├── Program.cs
│       ├── appsettings.json
│       └── BancaAdaptativa.Api.csproj
└── tests/
    └── BancaAdaptativa.Api.Tests/
```

Si la estructura ya existe, OpenCode debe respetarla.

---

# REGLA CRÍTICA: Manejo de fechas y horas

Esta sección es obligatoria.

## 1. Prohibido usar tiempo local del servidor o del usuario

En backend queda prohibido usar:

```csharp
DateTime.Now
DateTime.Today
DateTime.LocalNow
ToLocalTime()
DateTimeOffset.Now
```

También se debe evitar cualquier lógica que tome la hora local del navegador o dispositivo del usuario como fuente de verdad para guardar registros.

---

## 2. Todo instante debe manejarse en UTC

Para campos que representan un instante exacto, por ejemplo:

```text
createdAt
startedAt
endedAt
updatedAt
confirmedAt
matchedAt
retentionUntil
```

Se debe usar:

```csharp
DateTime.Kind = DateTimeKind.Utc
```

o, si el proveedor lo soporta correctamente, `DateTimeOffset` en UTC.

Para SQLite, si `DateTimeOffset` genera problemas, usar `DateTime` siempre con `DateTimeKind.Utc`.

---

## 3. El servidor es la fuente de verdad

El backend debe asignar las fechas importantes.

Ejemplos:

```text
User.CreatedAt
Session.StartedAt
Session.EndedAt
MemoryEvent.CreatedAt
Transfer.ConfirmedAt
TransferConfirmation.ConfirmedAt
AuditLog.CreatedAt
ReconciliationMatch.MatchedAt
AccessibilityPreference.UpdatedAt
UserProfile.UpdatedAt
DetectedPreference.UpdatedAt
```

El cliente/frontend no debe enviar estas fechas para que se guarden directamente.

Si un DTO de creación contiene campos como:

```text
createdAt
confirmedAt
matchedAt
```

OpenCode debe eliminarlos del DTO de entrada o ignorarlos en el backend.

---

## 4. Usar TimeProvider

OpenCode debe registrar `TimeProvider.System` en el contenedor de dependencias:

```csharp
builder.Services.AddSingleton(TimeProvider.System);
```

Y debe usar `TimeProvider` para obtener la hora actual en servicios, endpoints y seeders.

Ejemplo:

```csharp
var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
```

Esto permite:

- obtener siempre UTC,
- facilitar pruebas,
- evitar `DateTime.Now`,
- mantener consistencia.

---

## 5. Respuestas JSON con fechas ISO 8601 UTC

La API debe devolver fechas en formato ISO 8601 UTC.

Ejemplo correcto:

```json
{
  "createdAt": "2026-06-16T18:30:00Z"
}
```

Ejemplo correcto para una fecha calendario:

```json
{
  "date": "2026-06-16"
}
```

No se deben devolver fechas ambiguas como:

```json
{
  "createdAt": "2026-06-16 18:30:00"
}
```

---

## 6. Fechas calendario puras

Para campos que son solo fecha, sin hora:

```text
Transaction.date
DailyBalance.date
```

Se debe usar:

```csharp
DateOnly
```

Estos campos representan un día calendario, no un instante UTC.

Ejemplo:

```csharp
public DateOnly Date { get; set; }
```

En JSON se serializa como:

```json
"date": "2026-06-16"
```

---

## 7. Fecha de negocio para balance diario

El balance diario necesita una regla de negocio.

OpenCode debe agregar en `appsettings.json`:

```json
{
  "Business": {
    "TimeZoneId": "America/Mexico_City"
  }
}
```

Cuando se calcule el día actual para balance diario, se debe usar esa zona horaria de negocio, no la zona horaria del dispositivo del usuario.

Ejemplo conceptual:

```csharp
var timeZone = TimeZoneInfo.FindSystemTimeZoneById("America/Mexico_City");
var businessToday = TimeZoneInfo.ConvertTimeFromUtc(DateTime.UtcNow, timeZone).Date;
```

Esto evita que usuarios en distintas zonas horarias alteren el cálculo del día bancario.

---

## 8. Endpoint de sincronización horaria

OpenCode debe agregar un endpoint simple:

```text
GET /server-time
```

Respuesta esperada:

```json
{
  "serverTimeUtc": "2026-06-16T18:30:00Z",
  "unixMilliseconds": 1781029800000
}
```

Esto permite que el frontend calcule diferencias horarias si lo necesita.

El frontend nunca debe usar su reloj local como fuente de verdad para crear registros importantes.

---

## 9. Sincronización del servidor

OpenCode no puede controlar completamente el reloj del sistema operativo, pero debe documentar que el servidor debe tener sincronización NTP activa.

Agregar en README o en un documento:

```text
El servidor debe tener sincronización horaria automática/NTP activa.
La API usa UTC como fuente de verdad.
El frontend solo convierte UTC a hora local para mostrarla.
```

---

# Modelo de datos requerido

OpenCode debe generar o corregir las entidades basándose en el diagrama E-R.

Las entidades son:

```text
User
UserProfile
AccessibilityPreference
Session
MemoryEvent
DetectedPreference
Account
Transaction
DailyBalance
Transfer
TransferConfirmation
ReconciliationMatch
AuditLog
```

---

## Convenciones de tipos

### IDs

Usar:

```csharp
int
```

para claves primarias.

---

### Dinero

Aunque el diagrama use `float`, OpenCode debe usar:

```csharp
decimal
```

para campos monetarios:

```text
Account.balance
Transaction.amount
DailyBalance.openingBalance
DailyBalance.income
DailyBalance.expenses
DailyBalance.closingBalance
Transfer.amount
```

Motivo: precisión financiera.

---

### Fechas calendario

Usar:

```csharp
DateOnly
```

para:

```text
Transaction.date
DailyBalance.date
```

---

### Instantes

Usar:

```csharp
DateTime
```

con `DateTimeKind.Utc` para:

```text
createdAt
startedAt
endedAt
updatedAt
confirmedAt
matchedAt
retentionUntil
```

---

### Campos opcionales

Se recomienda hacer nullable los campos que dependen de un evento futuro:

```text
Session.endedAt
Transfer.confirmedAt
TransferConfirmation.confirmedAt
ReconciliationMatch.matchedAt
MemoryEvent.retentionUntil
```

Ejemplo:

```csharp
public DateTime? ConfirmedAt { get; set; }
```

---

# Entidades esperadas

OpenCode debe asegurar que existan estas entidades con propiedades similares.

## User

```csharp
public class User
{
    public int IdUser { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Locale { get; set; } = "es-MX";
    public string Status { get; set; } = "active";
    public DateTime CreatedAt { get; set; }

    public UserProfile? UserProfile { get; set; }
    public AccessibilityPreference? AccessibilityPreference { get; set; }

    public ICollection<Account> Accounts { get; set; } = new List<Account>();
    public ICollection<Session> Sessions { get; set; } = new List<Session>();
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
    public ICollection<DetectedPreference> DetectedPreferences { get; set; } = new List<DetectedPreference>();
    public ICollection<Transfer> Transfers { get; set; } = new List<Transfer>();
    public ICollection<AuditLog> AuditLogs { get; set; } = new List<AuditLog>();
}
```

---

## UserProfile

```csharp
public class UserProfile
{
    public int IdProfile { get; set; }
    public int IdUser { get; set; }
    public int Age { get; set; }
    public string DisabilityType { get; set; } = string.Empty;
    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
}
```

---

## AccessibilityPreference

```csharp
public class AccessibilityPreference
{
    public int IdPreference { get; set; }
    public int IdUser { get; set; }

    public float FontScale { get; set; } = 1.0f;
    public bool HighContrast { get; set; }
    public bool DarkMode { get; set; }
    public bool ReducedMotion { get; set; }
    public bool LargeTargets { get; set; }
    public bool PlainLanguage { get; set; }

    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
}
```

---

## Session

```csharp
public class Session
{
    public int IdSession { get; set; }
    public int IdUser { get; set; }

    public DateTime StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }
    public string DeviceContext { get; set; } = string.Empty;

    public User User { get; set; } = null!;
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
}
```

---

## MemoryEvent

```csharp
public class MemoryEvent
{
    public int IdEvent { get; set; }
    public int IdSession { get; set; }
    public int IdUser { get; set; }
    public int? IdDetectedPreference { get; set; }

    public string EventType { get; set; } = string.Empty;
    public string Intent { get; set; } = string.Empty;
    public string TargetElement { get; set; } = string.Empty;
    public string RedactedSummary { get; set; } = string.Empty;
    public string SensitivityLevel { get; set; } = "low";

    public DateTime CreatedAt { get; set; }
    public DateTime? RetentionUntil { get; set; }

    public Session Session { get; set; } = null!;
    public User User { get; set; } = null!;
    public DetectedPreference? DetectedPreference { get; set; }
}
```

---

## DetectedPreference

```csharp
public class DetectedPreference
{
    public int IdDetected { get; set; }
    public int IdUser { get; set; }

    public string PreferenceType { get; set; } = string.Empty;
    public string Value { get; set; } = string.Empty;

    public float ConfidenceScore { get; set; }
    public int BasedOnEventsCount { get; set; }

    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
}
```

---

## Account

```csharp
public class Account
{
    public int IdAccount { get; set; }
    public int IdUser { get; set; }

    public string AccountType { get; set; } = string.Empty;
    public string Alias { get; set; } = string.Empty;
    public string MaskedNumber { get; set; } = string.Empty;
    public string Currency { get; set; } = "MXN";

    public decimal Balance { get; set; }

    public string Status { get; set; } = "active";
    public DateTime CreatedAt { get; set; }

    public User User { get; set; } = null!;

    public ICollection<Transaction> Transactions { get; set; } = new List<Transaction>();
    public ICollection<DailyBalance> DailyBalances { get; set; } = new List<DailyBalance>();
    public ICollection<Transfer> Transfers { get; set; } = new List<Transfer>();
}
```

---

## Transaction

```csharp
public class Transaction
{
    public int IdTransaction { get; set; }
    public int IdAccount { get; set; }

    public DateOnly Date { get; set; }

    public decimal Amount { get; set; }
    public string Direction { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public string Reference { get; set; } = string.Empty;

    public Account Account { get; set; } = null!;
    public ReconciliationMatch? ReconciliationMatch { get; set; }
}
```

---

## DailyBalance

```csharp
public class DailyBalance
{
    public int IdBalance { get; set; }
    public int IdAccount { get; set; }

    public DateOnly Date { get; set; }

    public decimal OpeningBalance { get; set; }
    public decimal Income { get; set; }
    public decimal Expenses { get; set; }
    public decimal ClosingBalance { get; set; }

    public Account Account { get; set; } = null!;
}
```

---

## Transfer

```csharp
public class Transfer
{
    public int IdTransfer { get; set; }
    public int IdUser { get; set; }
    public int IdOriginAccount { get; set; }

    public string DestinationAlias { get; set; } = string.Empty;
    public string DestinationMasked { get; set; } = string.Empty;

    public decimal Amount { get; set; }
    public string Currency { get; set; } = "MXN";
    public string Concept { get; set; } = string.Empty;
    public string Status { get; set; } = "pending";

    public string IdempotencyKey { get; set; } = Guid.NewGuid().ToString();

    public DateTime? ConfirmedAt { get; set; }

    public User User { get; set; } = null!;
    public Account OriginAccount { get; set; } = null!;

    public ICollection<TransferConfirmation> Confirmations { get; set; } = new List<TransferConfirmation>();
    public ReconciliationMatch? ReconciliationMatch { get; set; }
}
```

---

## TransferConfirmation

```csharp
public class TransferConfirmation
{
    public int IdConfirmation { get; set; }
    public int IdTransfer { get; set; }

    public string Method { get; set; } = string.Empty;
    public string Status { get; set; } = "pending";

    public DateTime? ConfirmedAt { get; set; }

    public Transfer Transfer { get; set; } = null!;
}
```

---

## ReconciliationMatch

```csharp
public class ReconciliationMatch
{
    public int IdMatch { get; set; }
    public int IdTransfer { get; set; }
    public int IdTransaction { get; set; }

    public string Status { get; set; } = "pending";
    public float MatchScore { get; set; }

    public DateTime? MatchedAt { get; set; }
    public string Notes { get; set; } = string.Empty;

    public Transfer Transfer { get; set; } = null!;
    public Transaction Transaction { get; set; } = null!;
}
```

---

## AuditLog

```csharp
public class AuditLog
{
    public int IdLog { get; set; }
    public int IdUser { get; set; }

    public string Action { get; set; } = string.Empty;
    public string Resource { get; set; } = string.Empty;
    public string Result { get; set; } = string.Empty;
    public string RiskLevel { get; set; } = "low";
    public string RedactedPayload { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public User User { get; set; } = null!;
}
```

---

# DbContext requerido

OpenCode debe crear o corregir:

```text
backend/src/BancaAdaptativa.Api/Data/AppDbContext.cs
```

Debe incluir:

```csharp
DbSet<User>
DbSet<UserProfile>
DbSet<AccessibilityPreference>
DbSet<Session>
DbSet<MemoryEvent>
DbSet<DetectedPreference>
DbSet<Account>
DbSet<Transaction>
DbSet<DailyBalance>
DbSet<Transfer>
DbSet<TransferConfirmation>
DbSet<ReconciliationMatch>
DbSet<AuditLog>
```

---

## Relaciones obligatorias

OpenCode debe configurar:

### User - UserProfile

Relación uno a uno.

Índice único:

```csharp
UserProfile.IdUser
```

---

### User - AccessibilityPreference

Relación uno a uno.

Índice único:

```csharp
AccessibilityPreference.IdUser
```

---

### Session - MemoryEvent

Relación uno a muchos.

Borrado en cascada desde Session.

---

### MemoryEvent - DetectedPreference

Relación opcional muchos a uno.

`MemoryEvent.IdDetectedPreference` debe ser nullable.

---

### Account - Transaction

Relación uno a muchos.

---

### Account - DailyBalance

Relación uno a muchos.

Índice único compuesto:

```csharp
{ IdAccount, Date }
```

---

### Account - Transfer

Relación uno a muchos para cuenta origen.

OpenCode debe evitar cascadas problemáticas.

Recomendado:

```csharp
OnDelete(DeleteBehavior.Restrict)
```

---

### Transfer - TransferConfirmation

Relación uno a muchos.

---

### Transfer - ReconciliationMatch

Relación uno a uno.

Índice único:

```csharp
ReconciliationMatch.IdTransfer
```

---

### Transaction - ReconciliationMatch

Relación uno a uno.

Índice único:

```csharp
ReconciliationMatch.IdTransaction
```

---

### User - AuditLog

Relación uno a muchos.

---

# Manejo de UTC en DbContext

OpenCode debe asegurar que todos los `DateTime` se traten como UTC.

Puede hacerlo con value converters, helper methods o convenciones claras.

Recomendación: agregar conversores para guardar como texto ISO 8601 UTC en SQLite.

Ejemplo conceptual:

```csharp
foreach (var entityType in modelBuilder.Model.GetEntityTypes())
{
    foreach (var property in entityType.GetProperties())
    {
        if (property.ClrType == typeof(DateTime))
        {
            // Convertir DateTime UTC a string ISO 8601 con Z
        }

        if (property.ClrType == typeof(DateTime?))
        {
            // Convertir DateTime? UTC a string ISO 8601 con Z
        }
    }
}
```

El objetivo es que al leer de SQLite el `DateTime.Kind` sea:

```csharp
DateTimeKind.Utc
```

y que al guardar se normalice a UTC.

---

# Program.cs requerido

OpenCode debe crear o corregir:

```text
backend/src/BancaAdaptativa.Api/Program.cs
```

Debe incluir:

```csharp
builder.Services.AddSingleton(TimeProvider.System);
```

Debe configurar:

```csharp
builder.Services.AddDbContext<AppDbContext>(...)
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddCors(...)
```

CORS debe permitir, al menos:

```text
http://localhost:3000
```

Debe aplicar migraciones al iniciar:

```csharp
db.Database.Migrate();
```

Debe ejecutar el seeder:

```csharp
DbSeeder.Seed(db, timeProvider);
```

Debe exponer:

```text
GET /
GET /health
GET /server-time
GET /accounts
GET /accounts/{accountId}/transactions
GET /accounts/{accountId}/daily-balances
```

---

## Endpoint /server-time

OpenCode debe implementar:

```text
GET /server-time
```

Ejemplo de implementación:

```csharp
app.MapGet("/server-time", (TimeProvider timeProvider) =>
{
    var now = timeProvider.GetUtcNow();

    return Results.Ok(new
    {
        serverTimeUtc = now.UtcDateTime,
        unixMilliseconds = now.ToUnixTimeMilliseconds()
    });
});
```

---

## Endpoint /health

OpenCode debe implementar:

```text
GET /health
```

Debe devolver:

```json
{
  "status": "ok",
  "serverTimeUtc": "2026-06-16T18:30:00Z",
  "dbPath": "..."
}
```

---

# Seeder requerido

OpenCode debe crear o corregir:

```text
backend/src/BancaAdaptativa.Api/Data/DbSeeder.cs
```

El seeder debe:

1. No duplicar datos si ya existen usuarios.
2. Usar UTC mediante `TimeProvider`.
3. Crear un usuario demo.
4. Crear perfil.
5. Crear preferencias de accesibilidad.
6. Crear una cuenta.
7. Crear movimientos.
8. Crear balance diario.
9. Crear una transferencia.
10. Crear una confirmación.
11. Crear una sesión.
12. Crear un evento de memoria.
13. Crear una preferencia detectada.
14. Crear auditoría.

Ejemplo de firma recomendada:

```csharp
public static class DbSeeder
{
    public static void Seed(AppDbContext db, TimeProvider timeProvider)
    {
        if (db.Users.Any()) return;

        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;

        // Seed data...
    }
}
```

No usar:

```csharp
DateTime.Now
```

Ni:

```csharp
DateTime.Today
```

Para `DateOnly` de movimiento o balance diario, usar algo como:

```csharp
var today = DateOnly.FromDateTime(nowUtc.Date);
```

Si se necesita fecha de negocio, usar la zona horaria configurada.

---

# Endpoints mínimos

OpenCode debe generar endpoints básicos para que la API pueda ser probada.

## Users

```text
GET /users/me
```

Debe devolver usuario demo actual, por ahora simulando `idUser = 1`.

---

## Preferencias

```text
GET /me/preferences
PUT /me/preferences
```

El PUT debe actualizar:

```text
fontScale
highContrast
darkMode
reducedMotion
largeTargets
plainLanguage
```

Al actualizar debe poner:

```csharp
UpdatedAt = timeProvider.GetUtcNow().UtcDateTime
```

---

## Accounts

```text
GET /accounts
GET /accounts/{accountId}
```

---

## Transactions

```text
GET /accounts/{accountId}/transactions
```

Soportar filtros opcionales:

```text
from
to
category
direction
status
search
limit
```

Donde `from` y `to` deben ser:

```csharp
DateOnly
```

---

## Daily balances

```text
GET /accounts/{accountId}/daily-balances
```

Soportar:

```text
from
to
```

---

## Transfers

```text
POST /transfers
GET /transfers/{transferId}
POST /transfers/{transferId}/confirm
```

El POST debe crear transferencia en estado:

```text
pending
```

Debe asignar:

```text
IdUser = 1
Status = pending
IdempotencyKey = client-provided or generated
```

No debe asignar `ConfirmedAt` en la creación.

El confirm debe:

1. Validar existencia.
2. Validar estado pendiente.
3. Actualizar estado a:

```text
confirmed
```

4. Asignar:

```text
ConfirmedAt = timeProvider.GetUtcNow().UtcDateTime
```

5. Crear:

```text
TransferConfirmation
```

6. Crear:

```text
AuditLog
```

---

## Reconciliation

```text
GET /reconciliation
```

Debe listar conciliaciones.

---

# DTOs

OpenCode debe crear DTOs en:

```text
backend/src/BancaAdaptativa.Api/Dtos/
```

No debe exponer entidades directamente si eso implica navegar relaciones grandes.

Para entradas, no debe aceptar fechas generadas por cliente para campos de auditoría.

Ejemplo prohibido:

```json
{
  "createdAt": "2026-06-16T18:30:00Z"
}
```

si ese campo debe ser generado por servidor.

---

# Migraciones

OpenCode debe verificar si ya existe una migración.

Si no existe:

```bash
dotnet ef migrations add InitialCreate --output-dir Data/Migrations
```

Si ya existe pero hay cambios por fechas/tipos:

```bash
dotnet ef migrations add UtcDateHandling
```

Luego:

```bash
dotnet ef database update
```

Si la base SQLite local está corrupta o incompatible durante desarrollo, OpenCode puede eliminar:

```text
backend/data/app.db
```

solo si es un entorno local/dev.

Nunca debe hacer esto en producción.

---

# Comandos esperados

OpenCode puede ejecutar, desde `backend/`:

```bash
dotnet restore
dotnet build
dotnet test
```

Desde `backend/src/BancaAdaptativa.Api`:

```bash
dotnet run --urls http://localhost:8000
```

Para Swagger:

```text
http://localhost:8000/swagger
```

Para health:

```text
http://localhost:8000/health
```

Para server time:

```text
http://localhost:8000/server-time
```

---

# Validaciones que OpenCode debe realizar

OpenCode debe buscar en el backend y corregir cualquier uso de:

```text
DateTime.Now
DateTime.Today
DateTime.LocalNow
ToLocalTime
DateTimeOffset.Now
```

Debe reemplazarlos por:

```csharp
timeProvider.GetUtcNow().UtcDateTime
```

o, si no hay `TimeProvider` disponible en ese contexto:

```csharp
DateTime.UtcNow
```

pero preferir siempre `TimeProvider`.

---

# Criterios de aceptación

OpenCode debe considerar terminado el trabajo cuando:

1. La solución compila sin errores.

2. La API levanta con:

```bash
dotnet run --urls http://localhost:8000
```

3. Swagger está disponible.

4. La base SQLite se crea correctamente.

5. Las migraciones aplican.

6. El seeder inserta datos demo.

7. Todas las fechas de auditoría se guardan en UTC.

8. La API devuelve fechas con formato ISO 8601 UTC.

9. Existe el endpoint:

```text
GET /server-time
```

10. No existen usos de:

```text
DateTime.Now
DateTime.Today
ToLocalTime()
```

en código de backend.

11. `Transaction.date` y `DailyBalance.date` usan `DateOnly`.

12. El dinero usa `decimal`.

13. Las relaciones uno a uno tienen índices únicos.

14. `Transfer.IdempotencyKey` tiene índice único.

15. `DailyBalance` tiene índice único por cuenta y fecha.

16. El frontend no necesita enviar fechas de auditoría.

17. El servidor asigna fechas críticas.

---

# Nota para frontend

Aunque esta tarea es backend, OpenCode puede dejar documentado lo siguiente:

```text
El frontend debe mostrar las fechas UTC convertidas a la zona local del navegador solo para visualización.

Ejemplo JavaScript:

new Date(value)

Nunca debe usar new Date() del dispositivo como fuente de verdad para crear registros importantes.
```

---

# Nota final de arquitectura

La API debe ser language-agnostic para los consumidores.

El frontend Next.js, el servidor MCP y la capa de integración solo deben preocuparse por:

```text
HTTP + JSON + OpenAPI
```

No debe importarles internamente si el backend usa:

```text
Python
.NET
Node
Java
```

siempre que el contrato se respete.

En este caso, el backend será .NET 10.
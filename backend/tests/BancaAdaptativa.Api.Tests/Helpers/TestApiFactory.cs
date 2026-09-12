using BancaAdaptativa.Api.Data;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Time.Testing;

namespace BancaAdaptativa.Api.Tests.Helpers;

/// <summary>
/// Factory de integración: SQLite en archivo temporal + FakeTimeProvider + JWT de test.
/// Cada instancia es aislada (archivo propio). Program.Migrate()+Seed corren sobre ese archivo.
/// </summary>
public sealed class TestApiFactory : WebApplicationFactory<Program>, IDisposable
{
    public FakeTimeProvider FakeTime { get; } =
        new FakeTimeProvider(DateTimeOffset.UtcNow);

    private readonly string _dbFile =
        Path.Combine(Path.GetTempPath(), $"banca-test-{Guid.NewGuid():N}.db");

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        // Program.cs captura Jwt:Key al arrancar para validación; el env var garantiza
        // que creación (AuthService) y validación (JwtBearer) usen la misma clave.
        Environment.SetEnvironmentVariable("JWT_KEY", "test-key-32-chars-minimo-1234567890");
        builder.UseEnvironment("Testing");
        builder.ConfigureAppConfiguration((_, cfg) =>
        {
            cfg.AddInMemoryCollection(new Dictionary<string, string?>
            {
                ["ConnectionStrings:Default"] = $"Data Source={_dbFile}",
                ["Jwt:Key"] = "test-key-32-chars-minimo-1234567890",
                ["Jwt:Issuer"] = "banca-adaptativa",
                ["Jwt:Audience"] = "banca-clients",
                ["Jwt:ExpiresMinutes"] = "60",
                ["Business:TimeZoneId"] = "America/Mexico_City",
            });
        });
        builder.ConfigureServices(services =>
        {
            var tp = services.SingleOrDefault(d => d.ServiceType == typeof(TimeProvider));
            if (tp is not null) services.Remove(tp);
            services.AddSingleton<TimeProvider>(FakeTime);
        });
    }

    public new void Dispose()
    {
        base.Dispose();
        try { if (File.Exists(_dbFile)) File.Delete(_dbFile); } catch { /* best effort */ }
    }
}

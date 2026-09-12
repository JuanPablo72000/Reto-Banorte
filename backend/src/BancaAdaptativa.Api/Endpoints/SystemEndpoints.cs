using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Common;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Endpoints;

public static class SystemEndpoints
{
    public static void MapSystem(this IEndpointRouteBuilder app)
    {
        app.MapGet("/", () => Results.Ok(new { name = "BancaAdaptativa.Api", version = "1.0" }));

        app.MapGet("/health", async (AppDbContext db, TimeProvider time, IConfiguration config) =>
        {
            var canConnect = await db.Database.CanConnectAsync();
            return Results.Ok(new HealthResponse(
                canConnect ? "ok" : "degraded",
                time.GetUtcNow().UtcDateTime,
                config.GetConnectionString("Default") ?? ""));
        });

        app.MapGet("/server-time", (TimeProvider time) =>
        {
            var now = time.GetUtcNow();
            return Results.Ok(new ServerTimeResponse(now.UtcDateTime, now.ToUnixTimeMilliseconds()));
        });
    }
}

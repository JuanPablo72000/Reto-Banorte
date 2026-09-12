using BancaAdaptativa.Api.Dtos.Auth;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class AuthEndpoints
{
    public static void MapAuth(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/auth").WithTags("Auth");

        g.MapPost("/register", async (RegisterRequest req, IAuthService auth, CancellationToken ct) =>
        {
            try { return Results.Created("/users/me", await auth.RegisterAsync(req, ct)); }
            catch (InvalidOperationException ex) when (ex.Message == "EMAIL_TAKEN")
            { return Results.Conflict(new { error = "EMAIL_TAKEN" }); }
        });

        g.MapPost("/login", async (LoginRequest req, IAuthService auth, CancellationToken ct) =>
        {
            try { return Results.Ok(await auth.LoginAsync(req, ct)); }
            catch (UnauthorizedAccessException)
            { return Results.Unauthorized(); }
        });
    }
}

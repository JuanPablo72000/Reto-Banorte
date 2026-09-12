using System.Security.Claims;
using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Auth;
using BancaAdaptativa.Api.Dtos.Preferences;
using BancaAdaptativa.Api.Services;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Endpoints;

public static class UserEndpoints
{
    public static void MapUsers(this IEndpointRouteBuilder app)
    {
        app.MapGet("/users/me", async (ClaimsPrincipal user, AppDbContext db, CancellationToken ct) =>
        {
            var id = user.GetUserId();
            var u = await db.Users.AsNoTracking().FirstOrDefaultAsync(x => x.IdUser == id, ct);
            return u is null ? Results.NotFound() : Results.Ok(new UserDto(u.IdUser, u.Name, u.Email, u.Locale, u.Status, u.CreatedAt));
        }).RequireAuthorization().WithTags("Users")
            .WithName("getMe")
            .WithSummary("Obtiene el usuario autenticado")
            .Produces<UserDto>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        var prefs = app.MapGroup("/me/preferences").RequireAuthorization().WithTags("Preferences");
        prefs.MapGet("/", async (ClaimsPrincipal user, IPreferenceService svc, CancellationToken ct) =>
            Results.Ok(await svc.GetAsync(user.GetUserId(), ct)))
            .WithName("getMePreferences")
            .WithSummary("Obtiene las preferencias de accesibilidad")
            .Produces<AccessibilityPreferenceResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);
        prefs.MapPut("/", async (ClaimsPrincipal user, UpdatePreferencesRequest req, IPreferenceService svc, CancellationToken ct) =>
            Results.Ok(await svc.UpdateAsync(user.GetUserId(), req, ct)))
            .WithName("updateMePreferences")
            .WithSummary("Actualiza las preferencias de accesibilidad")
            .Produces<AccessibilityPreferenceResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);
    }
}

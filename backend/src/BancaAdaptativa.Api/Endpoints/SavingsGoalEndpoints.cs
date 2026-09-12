using System.Security.Claims;
using BancaAdaptativa.Api.Dtos.SavingsGoals;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class SavingsGoalEndpoints
{
    public static void MapSavingsGoals(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/me/savings-goals").RequireAuthorization().WithTags("SavingsGoals");

        g.MapPost("/", async (CreateSavingsGoalRequest req, ClaimsPrincipal user, ISavingsGoalService svc, CancellationToken ct) =>
            Results.Created("/me/savings-goals", await svc.CreateAsync(user.GetUserId(), req, ct)))
            .WithName("createSavingsGoal")
            .WithSummary("Crea una meta de ahorro")
            .Produces<SavingsGoalResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/", async (ClaimsPrincipal user, ISavingsGoalService svc, string? status, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), status, ct)))
            .WithName("getSavingsGoals")
            .WithSummary("Lista las metas de ahorro")
            .Produces<IReadOnlyList<SavingsGoalResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapPost("/{goalId:int}/contribute", async (int goalId, ContributeSavingsGoalRequest req, ClaimsPrincipal user, ISavingsGoalService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.ContributeAsync(user.GetUserId(), goalId, req.Amount, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (InvalidOperationException ex) { return Results.Conflict(new { error = ex.Message }); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_AMOUNT" }); }
        });

        g.MapPut("/{goalId:int}/status", async (int goalId, string status, ClaimsPrincipal user, ISavingsGoalService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.SetStatusAsync(user.GetUserId(), goalId, status, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_STATUS" }); }
        });

        g.MapDelete("/{goalId:int}", async (int goalId, ClaimsPrincipal user, ISavingsGoalService svc, CancellationToken ct) =>
        {
            try { await svc.DeleteAsync(user.GetUserId(), goalId, ct); return Results.NoContent(); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });
    }
}

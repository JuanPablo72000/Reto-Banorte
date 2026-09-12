using System.Security.Claims;
using BancaAdaptativa.Api.Dtos.Budgets;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class BudgetEndpoints
{
    public static void MapBudgets(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/me/budgets").RequireAuthorization().WithTags("Budgets");

        g.MapPost("/", async (CreateBudgetRequest req, ClaimsPrincipal user, IBudgetService svc, CancellationToken ct) =>
        {
            try { return Results.Created("/me/budgets", await svc.CreateOrUpdateAsync(user.GetUserId(), req, ct)); }
            catch (KeyNotFoundException) { return Results.BadRequest(new { error = "CATEGORY_NOT_FOUND" }); }
        });

        g.MapGet("/monthly", async (ClaimsPrincipal user, IBudgetService svc, int year, int month, CancellationToken ct) =>
            Results.Ok(await svc.MonthlySummaryAsync(user.GetUserId(), year, month, ct)));

        g.MapDelete("/{budgetId:int}", async (int budgetId, ClaimsPrincipal user, IBudgetService svc, CancellationToken ct) =>
        {
            try { await svc.DeleteAsync(user.GetUserId(), budgetId, ct); return Results.NoContent(); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });
    }
}

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
        })
            .WithName("createOrUpdateBudget")
            .WithSummary("Crea o actualiza un presupuesto mensual")
            .Produces<BudgetResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status400BadRequest)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/monthly", async (ClaimsPrincipal user, IBudgetService svc, int year, int month,
            string? category, string? status, CancellationToken ct) =>
            Results.Ok(await svc.MonthlySummaryAsync(user.GetUserId(), year, month, category, status, ct)))
            .WithName("getMonthlyBudgets")
            .WithSummary("Obtiene el resumen mensual de presupuestos")
            .Produces<BudgetMonthlySummaryResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapDelete("/{budgetId:int}", async (int budgetId, ClaimsPrincipal user, IBudgetService svc, CancellationToken ct) =>
        {
            try { await svc.DeleteAsync(user.GetUserId(), budgetId, ct); return Results.NoContent(); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("deleteBudget")
            .WithSummary("Elimina un presupuesto")
            .Produces(StatusCodes.Status204NoContent)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);
    }
}

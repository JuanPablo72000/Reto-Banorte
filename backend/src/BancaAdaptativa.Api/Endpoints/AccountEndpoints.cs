using System.Security.Claims;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class AccountEndpoints
{
    public static void MapAccounts(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("").RequireAuthorization().WithTags("Accounts");

        g.MapGet("/accounts", async (ClaimsPrincipal user, IAccountQueryService svc, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), ct)));

        g.MapGet("/accounts/{accountId:int}", async (int accountId, ClaimsPrincipal user, IAccountQueryService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetAsync(user.GetUserId(), accountId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapGet("/accounts/{accountId:int}/transactions", async (
            int accountId, ClaimsPrincipal user, IAccountQueryService svc,
            DateOnly? from, DateOnly? to, string? category, string? direction,
            string? status, string? search, int? limit, CancellationToken ct) =>
        {
            try
            {
                return Results.Ok(await svc.TransactionsAsync(user.GetUserId(), accountId, from, to, category, direction, status, search, limit ?? 50, ct));
            }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapGet("/accounts/{accountId:int}/daily-balances", async (
            int accountId, ClaimsPrincipal user, IAccountQueryService svc,
            DateOnly? from, DateOnly? to, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.BalancesAsync(user.GetUserId(), accountId, from, to, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapGet("/reconciliation", async (ClaimsPrincipal user, IAccountQueryService svc, CancellationToken ct) =>
            Results.Ok(await svc.ReconciliationAsync(user.GetUserId(), ct)));

        g.MapGet("/accounts/{accountId:int}/statements", async (
            int accountId, ClaimsPrincipal user, IStatementService svc,
            int? year, int? month, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.ListAsync(user.GetUserId(), accountId, year, month, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapGet("/accounts/{accountId:int}/statements/{statementId:int}", async (
            int statementId, ClaimsPrincipal user, IStatementService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetDetailAsync(user.GetUserId(), statementId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapPost("/accounts/{accountId:int}/statements/generate", async (
            int accountId, ClaimsPrincipal user, IStatementService svc,
            int year, int month, int cutOffDay, CancellationToken ct) =>
        {
            try { return Results.Created($"/accounts/{accountId}/statements", await svc.GenerateAsync(user.GetUserId(), accountId, year, month, cutOffDay, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_RANGE" }); }
        });

        g.MapGet("/expense-categories", async (IStatementService svc, CancellationToken ct) =>
            Results.Ok(await svc.CategoriesAsync(ct)));
    }
}

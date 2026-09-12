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
    }
}

using System.Security.Claims;
using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Dtos.Reconciliation;
using BancaAdaptativa.Api.Dtos.Transactions;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class AccountEndpoints
{
    public static void MapAccounts(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("").RequireAuthorization().WithTags("Accounts");

        g.MapGet("/accounts", async (ClaimsPrincipal user, IAccountQueryService svc,
            string? status, string? accountType, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), status, accountType, ct)))
            .WithName("getAccounts")
            .WithSummary("Lista las cuentas del usuario autenticado")
            .Produces<IReadOnlyList<AccountResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/me/account-summary", async (ClaimsPrincipal user, IAccountQueryService svc, CancellationToken ct) =>
            Results.Ok(await svc.SummaryAsync(user.GetUserId(), ct)))
            .WithName("getMeAccountSummary")
            .WithSummary("Obtiene el saldo total y el desglose de cuentas")
            .Produces<AccountSummaryResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/accounts/{accountId:int}", async (int accountId, ClaimsPrincipal user, IAccountQueryService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetAsync(user.GetUserId(), accountId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getAccountById")
            .WithSummary("Obtiene una cuenta del usuario autenticado")
            .Produces<AccountResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/accounts/{accountId:int}/transactions", async (
            int accountId, ClaimsPrincipal user, IAccountQueryService svc,
            DateOnly? from, DateOnly? to, string? category, string? direction,
            string? status, string? search, int? limit, string? expenseCategory, CancellationToken ct) =>
        {
            try
            {
                return Results.Ok(await svc.TransactionsAsync(user.GetUserId(), accountId, from, to, category, direction, status, search, limit ?? 50, expenseCategory, ct));
            }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getAccountTransactions")
            .WithSummary("Lista los movimientos de una cuenta")
            .Produces<IReadOnlyList<TransactionResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/me/transactions", async (
            ClaimsPrincipal user, IAccountQueryService svc,
            int? accountId, DateOnly? from, DateOnly? to, string? category, string? expenseCategory,
            string? direction, string? status, string? search, int? limit, CancellationToken ct) =>
        {
            try
            {
                return Results.Ok(await svc.AllTransactionsAsync(user.GetUserId(), accountId, from, to, category, expenseCategory, direction, status, search, limit ?? 50, ct));
            }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getAllTransactions")
            .WithSummary("Lista los movimientos de todas las cuentas del usuario")
            .Produces<IReadOnlyList<TransactionResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/accounts/{accountId:int}/daily-balances", async (
            int accountId, ClaimsPrincipal user, IAccountQueryService svc,
            DateOnly? from, DateOnly? to, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.BalancesAsync(user.GetUserId(), accountId, from, to, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getAccountDailyBalances")
            .WithSummary("Lista los balances diarios de una cuenta")
            .Produces<IReadOnlyList<DailyBalanceResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/reconciliation", async (ClaimsPrincipal user, IAccountQueryService svc,
            string? status, CancellationToken ct) =>
            Results.Ok(await svc.ReconciliationAsync(user.GetUserId(), status, ct)))
            .WithName("getReconciliation")
            .WithSummary("Lista las conciliaciones del usuario")
            .Produces<IReadOnlyList<ReconciliationResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/accounts/{accountId:int}/statements", async (
            int accountId, ClaimsPrincipal user, IStatementService svc,
            int? year, int? month, string? status, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.ListAsync(user.GetUserId(), accountId, year, month, status, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getAccountStatements")
            .WithSummary("Lista los estados de cuenta de una cuenta")
            .Produces<IReadOnlyList<StatementResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/accounts/{accountId:int}/statements/{statementId:int}", async (
            int statementId, ClaimsPrincipal user, IStatementService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetDetailAsync(user.GetUserId(), statementId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getStatementDetail")
            .WithSummary("Obtiene el detalle y desglose de un estado de cuenta")
            .Produces<StatementDetailResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapPost("/accounts/{accountId:int}/statements/generate", async (
            int accountId, ClaimsPrincipal user, IStatementService svc,
            int year, int month, int cutOffDay, CancellationToken ct) =>
        {
            try { return Results.Created($"/accounts/{accountId}/statements", await svc.GenerateAsync(user.GetUserId(), accountId, year, month, cutOffDay, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_RANGE" }); }
        })
            .WithName("generateAccountStatement")
            .WithSummary("Genera un estado de cuenta")
            .Produces<StatementResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status400BadRequest)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapGet("/expense-categories", async (IStatementService svc, string? search, CancellationToken ct) =>
            Results.Ok(await svc.CategoriesAsync(search, ct)))
            .WithName("getExpenseCategories")
            .WithSummary("Lista las categorías de gasto")
            .Produces<IReadOnlyList<ExpenseCategoryResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);
    }
}

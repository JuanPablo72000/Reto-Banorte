using System.Security.Claims;
using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class CreditCardEndpoints
{
    public static void MapCreditCards(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("").RequireAuthorization().WithTags("CreditCards");

        g.MapPost("/me/credit-cards", async (CreateCreditCardRequest req, ClaimsPrincipal user, ICreditCardService svc, CancellationToken ct) =>
            Results.Created("/me/credit-cards", await svc.CreateAsync(user.GetUserId(), req, ct)));

        g.MapGet("/me/credit-cards", async (ClaimsPrincipal user, ICreditCardService svc, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), ct)));

        g.MapGet("/me/credit-cards/{cardId:int}/statements", async (int cardId, ClaimsPrincipal user, ICreditCardService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.StatementsAsync(user.GetUserId(), cardId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapPost("/me/credit-cards/{cardId:int}/statements/generate", async (
            int cardId, ClaimsPrincipal user, ICreditCardService svc,
            int year, int month, decimal totalPurchases, decimal totalPayments, CancellationToken ct) =>
        {
            try { return Results.Created($"/me/credit-cards/{cardId}/statements", await svc.GenerateStatementAsync(user.GetUserId(), cardId, year, month, totalPurchases, totalPayments, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_RANGE" }); }
        });

        g.MapPost("/me/credit-cards/{cardId:int}/pay", async (int cardId, PayCreditCardRequest req, ClaimsPrincipal user, ICreditCardService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.PayAsync(user.GetUserId(), cardId, req.Amount, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_AMOUNT" }); }
        });
    }
}

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
            Results.Created("/me/credit-cards", await svc.CreateAsync(user.GetUserId(), req, ct)))
            .WithName("createCreditCard")
            .WithSummary("Registra una tarjeta de crédito")
            .Produces<CreditCardResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/me/credit-cards", async (ClaimsPrincipal user, ICreditCardService svc,
            string? status, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), status, ct)))
            .WithName("getCreditCards")
            .WithSummary("Lista las tarjetas de crédito")
            .Produces<IReadOnlyList<CreditCardResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/me/credit-cards/{cardId:int}/statements", async (int cardId, ClaimsPrincipal user, ICreditCardService svc,
            int? year, int? month, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.StatementsAsync(user.GetUserId(), cardId, year, month, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getCreditCardStatements")
            .WithSummary("Lista los estados de cuenta de una tarjeta")
            .Produces<IReadOnlyList<CreditCardStatementResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapPost("/me/credit-cards/{cardId:int}/statements/generate", async (
            int cardId, ClaimsPrincipal user, ICreditCardService svc,
            int year, int month, decimal totalPurchases, decimal totalPayments, CancellationToken ct) =>
        {
            try { return Results.Created($"/me/credit-cards/{cardId}/statements", await svc.GenerateStatementAsync(user.GetUserId(), cardId, year, month, totalPurchases, totalPayments, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_RANGE" }); }
        })
            .WithName("generateCreditCardStatement")
            .WithSummary("Genera un estado de cuenta de tarjeta")
            .Produces<CreditCardStatementResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status400BadRequest)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapPost("/me/credit-cards/{cardId:int}/pay", async (int cardId, PayCreditCardRequest req, ClaimsPrincipal user, ICreditCardService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.PayAsync(user.GetUserId(), cardId, req.Amount, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (ArgumentOutOfRangeException ex) { return Results.BadRequest(new { error = ex.ParamName ?? "INVALID_AMOUNT" }); }
        })
            .WithName("payCreditCard")
            .WithSummary("Registra un pago de tarjeta de crédito")
            .Produces<CreditCardResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status400BadRequest)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);
    }
}

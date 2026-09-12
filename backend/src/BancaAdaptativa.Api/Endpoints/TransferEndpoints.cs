using System.Security.Claims;
using BancaAdaptativa.Api.Dtos.Transfers;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Endpoints;

public static class TransferEndpoints
{
    public static void MapTransfers(this IEndpointRouteBuilder app)
    {
        var g = app.MapGroup("/transfers").RequireAuthorization().WithTags("Transfers");

        g.MapPost("/", async (CreateTransferRequest req, ClaimsPrincipal user, ITransferService svc, CancellationToken ct) =>
        {
            try { return Results.Created("/transfers", await svc.CreateAsync(user.GetUserId(), req, ct)); }
            catch (KeyNotFoundException) { return Results.BadRequest(new { error = "ORIGIN_ACCOUNT_NOT_FOUND" }); }
        })
            .WithName("createTransfer")
            .WithSummary("Crea una transferencia pendiente")
            .Produces<TransferResponse>(StatusCodes.Status201Created)
            .Produces(StatusCodes.Status400BadRequest)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("", async (ClaimsPrincipal user, ITransferService svc,
            string? status, int? originAccountId, DateTime? from, DateTime? to, int? limit, CancellationToken ct) =>
            Results.Ok(await svc.ListAsync(user.GetUserId(), status, originAccountId, from, to, limit ?? 50, ct)))
            .WithName("getTransfers")
            .WithSummary("Lista las transferencias del usuario")
            .Produces<IReadOnlyList<TransferResponse>>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized);

        g.MapGet("/{transferId:int}", async (int transferId, ClaimsPrincipal user, ITransferService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetAsync(user.GetUserId(), transferId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        })
            .WithName("getTransferById")
            .WithSummary("Obtiene una transferencia")
            .Produces<TransferResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound);

        g.MapPost("/{transferId:int}/confirm", async (int transferId, ConfirmTransferRequest? req, ClaimsPrincipal user, ITransferService svc, CancellationToken ct) =>
        {
            try
            {
                var (t, c) = await svc.ConfirmAsync(user.GetUserId(), transferId, req?.Method ?? "app", ct);
                return Results.Ok(new ConfirmTransferResponse(t, c));
            }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (InvalidOperationException) { return Results.Conflict(new { error = "TRANSFER_NOT_PENDING" }); }
        })
            .WithName("confirmTransfer")
            .WithSummary("Confirma una transferencia pendiente")
            .Produces<ConfirmTransferResponse>(StatusCodes.Status200OK)
            .Produces(StatusCodes.Status401Unauthorized)
            .Produces(StatusCodes.Status404NotFound)
            .Produces(StatusCodes.Status409Conflict);
    }
}

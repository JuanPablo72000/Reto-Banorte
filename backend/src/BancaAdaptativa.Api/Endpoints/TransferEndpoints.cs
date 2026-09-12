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
        });

        g.MapGet("/{transferId:int}", async (int transferId, ClaimsPrincipal user, ITransferService svc, CancellationToken ct) =>
        {
            try { return Results.Ok(await svc.GetAsync(user.GetUserId(), transferId, ct)); }
            catch (KeyNotFoundException) { return Results.NotFound(); }
        });

        g.MapPost("/{transferId:int}/confirm", async (int transferId, ConfirmTransferRequest? req, ClaimsPrincipal user, ITransferService svc, CancellationToken ct) =>
        {
            try
            {
                var (t, c) = await svc.ConfirmAsync(user.GetUserId(), transferId, req?.Method ?? "app", ct);
                return Results.Ok(new { transfer = t, confirmation = c });
            }
            catch (KeyNotFoundException) { return Results.NotFound(); }
            catch (InvalidOperationException) { return Results.Conflict(new { error = "TRANSFER_NOT_PENDING" }); }
        });
    }
}

using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.Transfers;

public record CreateTransferRequest(
    [Required] int IdOriginAccount,
    [Required, MaxLength(60)] string DestinationAlias,
    [Required, MaxLength(20)] string DestinationMasked,
    [Range(0.01, 10000000)] decimal Amount,
    [MaxLength(5)] string Currency = "MXN",
    [MaxLength(140)] string Concept = "",
    [MaxLength(80)] string? IdempotencyKey = null);

public record TransferResponse(
    int IdTransfer, int IdOriginAccount, string DestinationAlias, string DestinationMasked,
    decimal Amount, string Currency, string Concept, string Status,
    string IdempotencyKey, DateTime? ConfirmedAt);

public record ConfirmTransferRequest([MaxLength(30)] string Method = "app");

public record TransferConfirmationResponse(int IdConfirmation, string Method, string Status, DateTime? ConfirmedAt);

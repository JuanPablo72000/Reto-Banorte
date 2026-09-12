namespace BancaAdaptativa.Api.Dtos.Accounts;

public record AccountSummaryResponse(
    decimal TotalBalance,
    string Currency,
    IReadOnlyList<AccountResponse> Accounts);

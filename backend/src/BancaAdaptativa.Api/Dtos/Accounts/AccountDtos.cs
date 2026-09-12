namespace BancaAdaptativa.Api.Dtos.Accounts;

public record AccountResponse(
    int IdAccount, string AccountType, string Alias, string MaskedNumber,
    string Currency, decimal Balance, string Status, DateTime CreatedAt);

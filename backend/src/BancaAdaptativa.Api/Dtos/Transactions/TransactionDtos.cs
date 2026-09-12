namespace BancaAdaptativa.Api.Dtos.Transactions;

public record TransactionResponse(
    int IdTransaction, DateOnly Date, decimal Amount, string Direction,
    string Category, string Description, string Status, string Reference);

public record DailyBalanceResponse(
    int IdBalance, DateOnly Date, decimal OpeningBalance, decimal Income,
    decimal Expenses, decimal ClosingBalance);

namespace BancaAdaptativa.Api.Dtos.Accounts;

public record StatementResponse(
    int IdStatement, int IdAccount, int CutOffDay,
    DateOnly PeriodStart, DateOnly PeriodEnd,
    decimal OpeningBalance, decimal ClosingBalance,
    decimal TotalCredits, decimal TotalDebits, int TransactionCount,
    string AccountType, string Status, DateTime GeneratedAt);

public record StatementExpenseBreakdown(
    int IdExpenseCategory, string CategoryName, string CategoryCode,
    decimal Amount, int TransactionCount,
    DateOnly? FirstTransactionDate, DateOnly? LastTransactionDate);

public record StatementDetailResponse(
    StatementResponse Statement,
    IReadOnlyList<StatementExpenseBreakdown> Expenses);

public record ExpenseCategoryResponse(
    int IdCategory, string Name, string Code, string Icon, bool IsDefault, int SortOrder);

using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.Budgets;

public record CreateBudgetRequest(
    [Required] int IdExpenseCategory,
    [Range(1, 12)] int Month,
    [Range(2000, 2100)] int Year,
    [Range(0.01, 10000000)] decimal AmountLimit);

public record BudgetResponse(
    int IdBudget, int IdExpenseCategory, string CategoryName, string CategoryCode,
    int Month, int Year, decimal AmountLimit, decimal CurrentSpent,
    decimal UsagePercent, string Status);

public record BudgetMonthlySummaryResponse(
    int Month, int Year, decimal TotalLimit, decimal TotalSpent,
    IReadOnlyList<BudgetResponse> Budgets);

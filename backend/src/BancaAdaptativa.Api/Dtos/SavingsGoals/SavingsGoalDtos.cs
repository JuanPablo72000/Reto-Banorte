using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.SavingsGoals;

public record CreateSavingsGoalRequest(
    [Required, MaxLength(100)] string Name,
    [Range(0.01, 100000000)] decimal TargetAmount,
    DateTime TargetDate);

public record SavingsGoalResponse(
    int IdGoal, string Name, decimal TargetAmount, decimal CurrentAmount,
    decimal ProgressPercent, DateTime TargetDate, string Status,
    DateTime CreatedAt, DateTime UpdatedAt);

public record ContributeSavingsGoalRequest(
    [Range(0.01, 10000000)] decimal Amount);

using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.SavingsGoals;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Services;

public interface ISavingsGoalService
{
    Task<SavingsGoalResponse> CreateAsync(int idUser, CreateSavingsGoalRequest req, CancellationToken ct = default);
    Task<IReadOnlyList<SavingsGoalResponse>> ListAsync(int idUser, CancellationToken ct = default);
    Task<SavingsGoalResponse> ContributeAsync(int idUser, int goalId, decimal amount, CancellationToken ct = default);
    Task<SavingsGoalResponse> SetStatusAsync(int idUser, int goalId, string status, CancellationToken ct = default);
    Task DeleteAsync(int idUser, int goalId, CancellationToken ct = default);
}

public class SavingsGoalService(AppDbContext db, TimeProvider timeProvider) : ISavingsGoalService
{
    private static SavingsGoalResponse Map(SavingsGoal g)
    {
        var pct = g.TargetAmount <= 0 ? 0 : Math.Round(g.CurrentAmount / g.TargetAmount * 100, 2);
        return new(g.IdGoal, g.Name, g.TargetAmount, g.CurrentAmount, pct,
            g.TargetDate, g.Status, g.CreatedAt, g.UpdatedAt);
    }

    public async Task<SavingsGoalResponse> CreateAsync(int idUser, CreateSavingsGoalRequest req, CancellationToken ct = default)
    {
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var g = new SavingsGoal
        {
            IdUser = idUser,
            Name = req.Name.Trim(),
            TargetAmount = req.TargetAmount,
            CurrentAmount = 0m,
            TargetDate = req.TargetDate.Kind == DateTimeKind.Utc ? req.TargetDate : req.TargetDate.ToUniversalTime(),
            Status = "active",
            CreatedAt = nowUtc,
            UpdatedAt = nowUtc
        };
        db.SavingsGoals.Add(g);
        await db.SaveChangesAsync(ct);
        return Map(g);
    }

    public async Task<IReadOnlyList<SavingsGoalResponse>> ListAsync(int idUser, CancellationToken ct = default) =>
        await db.SavingsGoals.AsNoTracking().Where(g => g.IdUser == idUser)
            .OrderBy(g => g.IdGoal)
            .Select(g => new SavingsGoalResponse(g.IdGoal, g.Name, g.TargetAmount, g.CurrentAmount,
                g.TargetAmount <= 0 ? 0 : Math.Round(g.CurrentAmount / g.TargetAmount * 100, 2),
                g.TargetDate, g.Status, g.CreatedAt, g.UpdatedAt))
            .ToListAsync(ct);

    public async Task<SavingsGoalResponse> ContributeAsync(int idUser, int goalId, decimal amount, CancellationToken ct = default)
    {
        if (amount <= 0) throw new ArgumentOutOfRangeException(nameof(amount), "AMOUNT_MUST_BE_POSITIVE");
        var g = await db.SavingsGoals.FirstOrDefaultAsync(x => x.IdGoal == goalId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("GOAL_NOT_FOUND");
        if (g.Status != "active") throw new InvalidOperationException("GOAL_NOT_ACTIVE");
        g.CurrentAmount += amount;
        if (g.CurrentAmount >= g.TargetAmount) g.Status = "completed";
        g.UpdatedAt = timeProvider.GetUtcNow().UtcDateTime;
        await db.SaveChangesAsync(ct);
        return Map(g);
    }

    public async Task<SavingsGoalResponse> SetStatusAsync(int idUser, int goalId, string status, CancellationToken ct = default)
    {
        var allowed = new[] { "active", "paused", "completed" };
        if (!allowed.Contains(status)) throw new ArgumentOutOfRangeException(nameof(status), "INVALID_STATUS");
        var g = await db.SavingsGoals.FirstOrDefaultAsync(x => x.IdGoal == goalId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("GOAL_NOT_FOUND");
        g.Status = status;
        g.UpdatedAt = timeProvider.GetUtcNow().UtcDateTime;
        await db.SaveChangesAsync(ct);
        return Map(g);
    }

    public async Task DeleteAsync(int idUser, int goalId, CancellationToken ct = default)
    {
        var g = await db.SavingsGoals.FirstOrDefaultAsync(x => x.IdGoal == goalId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("GOAL_NOT_FOUND");
        db.SavingsGoals.Remove(g);
        await db.SaveChangesAsync(ct);
    }
}

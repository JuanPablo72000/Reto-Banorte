using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Services;

public interface IStatementService
{
    Task<StatementResponse> GenerateAsync(int idUser, int accountId, int year, int month, int cutOffDay, CancellationToken ct = default);
    Task<IReadOnlyList<StatementResponse>> ListAsync(int idUser, int accountId, int? year, int? month, CancellationToken ct = default);
    Task<StatementDetailResponse> GetDetailAsync(int idUser, int statementId, CancellationToken ct = default);
    Task<IReadOnlyList<ExpenseCategoryResponse>> CategoriesAsync(CancellationToken ct = default);
}

public static class StatementPeriod
{
    /// <summary>
    /// Resuelve el periodo [PeriodStart, PeriodEnd] para un mes y día de corte.
    /// Si el día de corte excede los días del mes (p. ej. 31 en febrero),
    /// el corte se ajusta al último día del mes.
    /// </summary>
    public static (DateOnly Start, DateOnly End) Resolve(int year, int month, int cutOffDay)
    {
        cutOffDay = Math.Clamp(cutOffDay, 1, 31);
        var endDay = Math.Min(cutOffDay, DateTime.DaysInMonth(year, month));
        var end = new DateOnly(year, month, endDay);
        var prev = end.AddMonths(-1);
        var prevEndDay = Math.Min(cutOffDay, DateTime.DaysInMonth(prev.Year, prev.Month));
        var prevEnd = new DateOnly(prev.Year, prev.Month, prevEndDay);
        return (prevEnd.AddDays(1), end);
    }
}

public class StatementService(AppDbContext db, TimeProvider timeProvider, IBudgetService budgets) : IStatementService
{
    private static StatementResponse Map(Statement s) =>
        new(s.IdStatement, s.IdAccount, s.CutOffDay, s.PeriodStart, s.PeriodEnd,
            s.OpeningBalance, s.ClosingBalance, s.TotalCredits, s.TotalDebits,
            s.TransactionCount, s.AccountType, s.Status, s.GeneratedAt);

    private async Task<Account> RequireAccountAsync(int idUser, int accountId, CancellationToken ct)
    {
        var a = await db.Accounts.AsNoTracking().FirstOrDefaultAsync(x => x.IdAccount == accountId && x.IdUser == idUser, ct);
        return a ?? throw new KeyNotFoundException("ACCOUNT_NOT_FOUND");
    }

    public async Task<StatementResponse> GenerateAsync(int idUser, int accountId, int year, int month, int cutOffDay, CancellationToken ct = default)
    {
        var account = await RequireAccountAsync(idUser, accountId, ct);
        if (month < 1 || month > 12) throw new ArgumentOutOfRangeException(nameof(month), "MONTH_OUT_OF_RANGE");
        cutOffDay = Math.Clamp(cutOffDay, 1, 31);

        var (start, end) = StatementPeriod.Resolve(year, month, cutOffDay);

        var existing = await db.Statements.AsNoTracking()
            .FirstOrDefaultAsync(s => s.IdAccount == accountId && s.PeriodStart == start, ct);
        if (existing is not null) return Map(existing);

        var txs = await db.Transactions.AsNoTracking()
            .Where(t => t.IdAccount == accountId && t.Date >= start && t.Date <= end && t.Status == "posted")
            .ToListAsync(ct);

        var credits = txs.Where(t => t.Direction == "credit").Sum(t => t.Amount);
        var debits = txs.Where(t => t.Direction == "debit").Sum(t => t.Amount);

        var priorClose = await db.DailyBalances.AsNoTracking()
            .Where(d => d.IdAccount == accountId && d.Date < start)
            .OrderByDescending(d => d.Date)
            .Select(d => (decimal?)d.ClosingBalance)
            .FirstOrDefaultAsync(ct);
        var opening = priorClose ?? 0m;
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;

        var stmt = new Statement
        {
            IdAccount = accountId,
            CutOffDay = cutOffDay,
            PeriodStart = start,
            PeriodEnd = end,
            OpeningBalance = opening,
            ClosingBalance = opening + credits - debits,
            TotalCredits = credits,
            TotalDebits = debits,
            TransactionCount = txs.Count,
            AccountType = account.AccountType,
            Status = "generated",
            GeneratedAt = nowUtc
        };
        db.Statements.Add(stmt);
        await db.SaveChangesAsync(ct);

        // Desglose pre-computado de gastos por categoría (solo débitos con categoría asignada).
        var groups = txs
            .Where(t => t.Direction == "debit" && t.IdExpenseCategory.HasValue)
            .GroupBy(t => t.IdExpenseCategory!.Value)
            .ToList();
        foreach (var g in groups)
        {
            db.StatementExpenses.Add(new StatementExpense
            {
                IdStatement = stmt.IdStatement,
                IdExpenseCategory = g.Key,
                Amount = g.Sum(t => t.Amount),
                TransactionCount = g.Count(),
                FirstTransactionDate = g.Min(t => t.Date),
                LastTransactionDate = g.Max(t => t.Date)
            });
        }
        await db.SaveChangesAsync(ct);

        // Trigger: sincroniza presupuestos del mes de cierre con este statement.
        await budgets.SyncFromStatementAsync(idUser, stmt.IdStatement, ct);

        return Map(stmt);
    }

    public async Task<IReadOnlyList<StatementResponse>> ListAsync(int idUser, int accountId, int? year, int? month, CancellationToken ct = default)
    {
        await RequireAccountAsync(idUser, accountId, ct);
        var q = db.Statements.AsNoTracking().Where(s => s.IdAccount == accountId);
        if (year.HasValue) q = q.Where(s => s.PeriodEnd.Year == year.Value);
        if (month.HasValue) q = q.Where(s => s.PeriodEnd.Month == month.Value);
        return await q.OrderByDescending(s => s.PeriodEnd)
            .Select(s => new StatementResponse(s.IdStatement, s.IdAccount, s.CutOffDay, s.PeriodStart, s.PeriodEnd,
                s.OpeningBalance, s.ClosingBalance, s.TotalCredits, s.TotalDebits,
                s.TransactionCount, s.AccountType, s.Status, s.GeneratedAt))
            .ToListAsync(ct);
    }

    public async Task<StatementDetailResponse> GetDetailAsync(int idUser, int statementId, CancellationToken ct = default)
    {
        var s = await db.Statements.AsNoTracking()
            .Include(x => x.StatementExpenses).ThenInclude(e => e.ExpenseCategory)
            .Include(x => x.Account)
            .FirstOrDefaultAsync(x => x.IdStatement == statementId, ct);
        if (s is null || s.Account.IdUser != idUser) throw new KeyNotFoundException("STATEMENT_NOT_FOUND");
        var expenses = s.StatementExpenses
            .OrderByDescending(e => e.Amount)
            .Select(e => new StatementExpenseBreakdown(e.IdExpenseCategory, e.ExpenseCategory.Name,
                e.ExpenseCategory.Code, e.Amount, e.TransactionCount,
                e.FirstTransactionDate, e.LastTransactionDate))
            .ToList();
        return new(Map(s), expenses);
    }

    public async Task<IReadOnlyList<ExpenseCategoryResponse>> CategoriesAsync(CancellationToken ct = default) =>
        await db.ExpenseCategories.AsNoTracking().OrderBy(c => c.SortOrder)
            .Select(c => new ExpenseCategoryResponse(c.IdCategory, c.Name, c.Code, c.Icon, c.IsDefault, c.SortOrder))
            .ToListAsync(ct);
}

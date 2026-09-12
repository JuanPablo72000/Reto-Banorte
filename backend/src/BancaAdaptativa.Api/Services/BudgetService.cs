using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Budgets;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Services;

public interface IBudgetService
{
    Task<BudgetResponse> CreateOrUpdateAsync(int idUser, CreateBudgetRequest req, CancellationToken ct = default);
    Task<BudgetMonthlySummaryResponse> MonthlySummaryAsync(int idUser, int year, int month, CancellationToken ct = default);
    Task SyncFromStatementAsync(int idUser, int statementId, CancellationToken ct = default);
    Task DeleteAsync(int idUser, int budgetId, CancellationToken ct = default);
}

public class BudgetService(AppDbContext db, TimeProvider timeProvider) : IBudgetService
{
    private static BudgetResponse Map(Budget b, string name, string code)
    {
        var pct = b.AmountLimit <= 0 ? 0 : Math.Round(b.CurrentSpent / b.AmountLimit * 100, 2);
        return new(b.IdBudget, b.IdExpenseCategory, name, code, b.Month, b.Year,
            b.AmountLimit, b.CurrentSpent, pct, b.Status);
    }

    public async Task<BudgetResponse> CreateOrUpdateAsync(int idUser, CreateBudgetRequest req, CancellationToken ct = default)
    {
        var cat = await db.ExpenseCategories.AsNoTracking()
            .FirstOrDefaultAsync(c => c.IdCategory == req.IdExpenseCategory, ct)
            ?? throw new KeyNotFoundException("CATEGORY_NOT_FOUND");
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var monthStart = new DateTime(req.Year, req.Month, 1, 0, 0, 0, DateTimeKind.Utc);
        var monthEnd = monthStart.AddMonths(1).AddTicks(-1);

        var existing = await db.Budgets
            .FirstOrDefaultAsync(b => b.IdUser == idUser && b.IdExpenseCategory == req.IdExpenseCategory
                && b.Month == req.Month && b.Year == req.Year, ct);
        if (existing is not null)
        {
            existing.AmountLimit = req.AmountLimit;
            existing.UpdatedAt = nowUtc;
            existing.Status = existing.CurrentSpent >= req.AmountLimit ? "exceeded" : "active";
            await db.SaveChangesAsync(ct);
            return Map(existing, cat.Name, cat.Code);
        }

        // Gasto ya registrado en el mes calendario (triggers previos o transacciones posted).
        var start = DateOnly.FromDateTime(monthStart);
        var end = DateOnly.FromDateTime(monthEnd);
        var spent = await db.Transactions.AsNoTracking()
            .Where(t => t.Direction == "debit" && t.Status == "posted"
                && t.IdExpenseCategory == req.IdExpenseCategory && t.Date >= start && t.Date <= end
                && t.Account.IdUser == idUser)
            .SumAsync(t => (decimal?)t.Amount, ct) ?? 0m;

        var b = new Budget
        {
            IdUser = idUser,
            IdExpenseCategory = req.IdExpenseCategory,
            Month = req.Month,
            Year = req.Year,
            AmountLimit = req.AmountLimit,
            CurrentSpent = spent,
            StartDate = monthStart,
            EndDate = monthEnd,
            Status = spent >= req.AmountLimit ? "exceeded" : "active",
            CreatedAt = nowUtc,
            UpdatedAt = nowUtc
        };
        db.Budgets.Add(b);
        await db.SaveChangesAsync(ct);
        return Map(b, cat.Name, cat.Code);
    }

    public async Task<BudgetMonthlySummaryResponse> MonthlySummaryAsync(int idUser, int year, int month, CancellationToken ct = default)
    {
        var list = await db.Budgets.AsNoTracking()
            .Include(b => b.ExpenseCategory)
            .Where(b => b.IdUser == idUser && b.Year == year && b.Month == month)
            .OrderBy(b => b.ExpenseCategory.SortOrder)
            .ToListAsync(ct);
        var items = list.Select(b => Map(b, b.ExpenseCategory.Name, b.ExpenseCategory.Code)).ToList();
        return new(month, year, items.Sum(i => i.AmountLimit), items.Sum(i => i.CurrentSpent), items);
    }

    /// <summary>
    /// Trigger invocado al generar un statement: acumula el desglose de gastos
    /// en los presupuestos del mes de cierre (idempotente por statement).
    /// </summary>
    public async Task SyncFromStatementAsync(int idUser, int statementId, CancellationToken ct = default)
    {
        var stmt = await db.Statements.AsNoTracking()
            .Include(s => s.StatementExpenses)
            .FirstOrDefaultAsync(s => s.IdStatement == statementId, ct);
        if (stmt is null) throw new KeyNotFoundException("STATEMENT_NOT_FOUND");

        var month = stmt.PeriodEnd.Month;
        var year = stmt.PeriodEnd.Year;
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;

        foreach (var e in stmt.StatementExpenses)
        {
            var b = await db.Budgets.FirstOrDefaultAsync(x =>
                x.IdUser == idUser && x.IdExpenseCategory == e.IdExpenseCategory
                && x.Month == month && x.Year == year, ct);
            if (b is null) continue; // sin presupuesto para esa categoría: no se crea solo
            b.CurrentSpent += e.Amount;
            b.UpdatedAt = nowUtc;
            b.Status = b.CurrentSpent >= b.AmountLimit ? "exceeded" : "active";
        }
        await db.SaveChangesAsync(ct);
    }

    public async Task DeleteAsync(int idUser, int budgetId, CancellationToken ct = default)
    {
        var b = await db.Budgets.FirstOrDefaultAsync(x => x.IdBudget == budgetId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("BUDGET_NOT_FOUND");
        db.Budgets.Remove(b);
        await db.SaveChangesAsync(ct);
    }
}

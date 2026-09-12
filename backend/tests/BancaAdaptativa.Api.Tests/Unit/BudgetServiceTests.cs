using BancaAdaptativa.Api.Dtos.Budgets;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Tests.Unit;

public class BudgetServiceTests
{
    private static async Task<(TestDb t, int uid, int cat)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "B", Email = "b@b.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A",
            MaskedNumber = "****1", Currency = "MXN", Balance = 1000m,
            Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        var cat = new ExpenseCategory { Name = "Supermercados", Code = "supermarket", Icon = "cart", IsDefault = true, SortOrder = 6 };
        t.Db.ExpenseCategories.Add(cat);
        await t.Db.SaveChangesAsync();
        t.Db.Transactions.Add(new Transaction
        {
            IdAccount = acc.IdAccount, Date = new DateOnly(2026, 6, 5), Amount = 800m,
            Direction = "debit", Category = "super", Description = "Súper",
            Status = "posted", Reference = "S1", IdExpenseCategory = cat.IdCategory
        });
        await t.Db.SaveChangesAsync();
        return (t, u.IdUser, cat.IdCategory);
    }

    [Fact]
    public async Task CreateOrUpdate_CalculaGastadoInicial_YUpsert()
    {
        var (t, uid, cat) = await ArrangeAsync();
        using var _ = t;
        var svc = new BudgetService(t.Db, t.Time);

        var created = await svc.CreateOrUpdateAsync(uid, new CreateBudgetRequest(cat, 6, 2026, 5000m));
        Assert.Equal(800m, created.CurrentSpent);
        Assert.Equal(16m, created.UsagePercent);
        Assert.Equal("active", created.Status);

        var updated = await svc.CreateOrUpdateAsync(uid, new CreateBudgetRequest(cat, 6, 2026, 500m));
        Assert.Equal(created.IdBudget, updated.IdBudget); // upsert: mismo registro
        Assert.Equal("exceeded", updated.Status); // 800 >= 500
        Assert.Equal(1, await t.Db.Budgets.CountAsync());
    }

    [Fact]
    public async Task CreateOrUpdate_CategoriaInexistente_Lanza()
    {
        var (t, uid, _) = await ArrangeAsync();
        using var _2 = t;
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            new BudgetService(t.Db, t.Time).CreateOrUpdateAsync(uid, new CreateBudgetRequest(9999, 6, 2026, 100m)));
        Assert.Equal("CATEGORY_NOT_FOUND", ex.Message);
    }

    [Fact]
    public async Task SyncFromStatement_AcumulaGastoDelTrigger()
    {
        var (t, uid, cat) = await ArrangeAsync();
        using var _ = t;
        var budgets = new BudgetService(t.Db, t.Time);
        await budgets.CreateOrUpdateAsync(uid, new CreateBudgetRequest(cat, 6, 2026, 5000m));

        var statements = new StatementService(t.Db, t.Time, budgets);
        var acc = await t.Db.Accounts.Select(a => a.IdAccount).SingleAsync();
        var stmt = await statements.GenerateAsync(uid, acc, 2026, 6, 15); // dispara el trigger de sync

        var summary = await budgets.MonthlySummaryAsync(uid, 2026, 6);
        Assert.Equal(5000m, summary.TotalLimit);
        Assert.Equal(1600m, summary.TotalSpent); // 800 inicial + 800 del statement
        Assert.Equal("active", summary.Budgets.Single().Status);
    }

    [Fact]
    public async Task Delete_Elimina_YAjenoLanza()
    {
        var (t, uid, cat) = await ArrangeAsync();
        using var _ = t;
        var svc = new BudgetService(t.Db, t.Time);
        var created = await svc.CreateOrUpdateAsync(uid, new CreateBudgetRequest(cat, 6, 2026, 5000m));

        await Assert.ThrowsAsync<KeyNotFoundException>(() => svc.DeleteAsync(9999, created.IdBudget));
        await svc.DeleteAsync(uid, created.IdBudget);
        Assert.Empty(await t.Db.Budgets.ToListAsync());
    }
}

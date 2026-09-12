using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Unit;

public class StatementServiceTests
{
    private static async Task<(TestDb t, int uid, int acc, int catSuper, int catTrans)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "S", Email = "s@s.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A",
            MaskedNumber = "****1", Currency = "MXN", Balance = 1000m,
            Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        var super = new ExpenseCategory { Name = "Supermercados", Code = "supermarket", Icon = "cart", IsDefault = true, SortOrder = 6 };
        var trans = new ExpenseCategory { Name = "Transporte", Code = "transport", Icon = "transport", IsDefault = true, SortOrder = 7 };
        t.Db.ExpenseCategories.AddRange(super, trans);
        await t.Db.SaveChangesAsync();
        // Periodo con corte 15 en junio 2026: 2026-05-16 .. 2026-06-15
        t.Db.Transactions.AddRange(
            new Transaction { IdAccount = acc.IdAccount, Date = new DateOnly(2026, 6, 1), Amount = 5000m, Direction = "credit", Category = "nomina", Description = "Nómina", Status = "posted", Reference = "N1" },
            new Transaction { IdAccount = acc.IdAccount, Date = new DateOnly(2026, 6, 2), Amount = 800m, Direction = "debit", Category = "super", Description = "Súper", Status = "posted", Reference = "S1", IdExpenseCategory = super.IdCategory },
            new Transaction { IdAccount = acc.IdAccount, Date = new DateOnly(2026, 6, 3), Amount = 200m, Direction = "debit", Category = "transporte", Description = "Metro", Status = "posted", Reference = "T1", IdExpenseCategory = trans.IdCategory },
            new Transaction { IdAccount = acc.IdAccount, Date = new DateOnly(2026, 6, 4), Amount = 999m, Direction = "debit", Category = "super", Description = "Pendiente", Status = "pending", Reference = "P1", IdExpenseCategory = super.IdCategory },
            new Transaction { IdAccount = acc.IdAccount, Date = new DateOnly(2026, 7, 1), Amount = 50m, Direction = "debit", Category = "super", Description = "Fuera de periodo", Status = "posted", Reference = "F1", IdExpenseCategory = super.IdCategory });
        await t.Db.SaveChangesAsync();
        return (t, u.IdUser, acc.IdAccount, super.IdCategory, trans.IdCategory);
    }

    private static StatementService NewSvc(TestDb t) =>
        new(t.Db, t.Time, new BudgetService(t.Db, t.Time));

    [Fact]
    public async Task Generate_AgregaPostedDelPeriodo_YExcluyePendingYFueraDePeriodo()
    {
        var (t, uid, acc, _, _) = await ArrangeAsync();
        using var _2 = t;
        var r = await NewSvc(t).GenerateAsync(uid, acc, 2026, 6, 15);

        Assert.Equal(new DateOnly(2026, 5, 16), r.PeriodStart);
        Assert.Equal(new DateOnly(2026, 6, 15), r.PeriodEnd);
        Assert.Equal(5000m, r.TotalCredits);
        Assert.Equal(1000m, r.TotalDebits); // 800 + 200; pending y julio excluidos
        Assert.Equal(3, r.TransactionCount);
        Assert.Equal(0m, r.OpeningBalance);
        Assert.Equal(4000m, r.ClosingBalance);
        Assert.Equal("debito", r.AccountType);
        Assert.Equal("generated", r.Status);
    }

    [Fact]
    public async Task Generate_PrecomputaDesglosePorCategoria()
    {
        var (t, uid, acc, catSuper, catTrans) = await ArrangeAsync();
        using var _2 = t;
        var svc = NewSvc(t);
        var r = await svc.GenerateAsync(uid, acc, 2026, 6, 15);

        var detail = await svc.GetDetailAsync(uid, r.IdStatement);
        Assert.Equal(2, detail.Expenses.Count);
        var sup = detail.Expenses.Single(e => e.IdExpenseCategory == catSuper);
        Assert.Equal(800m, sup.Amount);
        Assert.Equal(new DateOnly(2026, 6, 2), sup.FirstTransactionDate);
        var tr = detail.Expenses.Single(e => e.IdExpenseCategory == catTrans);
        Assert.Equal(200m, tr.Amount);
    }

    [Fact]
    public async Task Generate_EsIdempotente()
    {
        var (t, uid, acc, _, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = NewSvc(t);
        var a = await svc.GenerateAsync(uid, acc, 2026, 6, 15);
        var b = await svc.GenerateAsync(uid, acc, 2026, 6, 15);
        Assert.Equal(a.IdStatement, b.IdStatement);
        Assert.Equal(1, t.Db.Statements.Count());
    }

    [Fact]
    public async Task Generate_Corte31EnFebrero_AjustaAlUltimoDia()
    {
        var (t, uid, acc, _, _) = await ArrangeAsync();
        using var _2 = t;
        // Febrero 2026 tiene 28 días: corte 31 -> 2026-02-28.
        // El periodo de enero cerró el 31-ene, así que febrero inicia el 1-feb.
        var r = await NewSvc(t).GenerateAsync(uid, acc, 2026, 2, 31);
        Assert.Equal(new DateOnly(2026, 2, 28), r.PeriodEnd);
        Assert.Equal(new DateOnly(2026, 2, 1), r.PeriodStart);
        Assert.Equal(31, r.CutOffDay); // se conserva el día configurado por el usuario
    }

    [Fact]
    public async Task Generate_CuentaAjena_LanzaNotFound()
    {
        var (t, _, acc, _, _) = await ArrangeAsync();
        using var _2 = t;
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            NewSvc(t).GenerateAsync(9999, acc, 2026, 6, 15));
        Assert.Equal("ACCOUNT_NOT_FOUND", ex.Message);
    }

    [Fact]
    public async Task List_FiltraPorAnioYMes()
    {
        var (t, uid, acc, _, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = NewSvc(t);
        await svc.GenerateAsync(uid, acc, 2026, 6, 15);
        await svc.GenerateAsync(uid, acc, 2026, 2, 31);

        Assert.Equal(2, (await svc.ListAsync(uid, acc, null, null)).Count);
        var feb = await svc.ListAsync(uid, acc, 2026, 2);
        Assert.Single(feb);
        Assert.Equal(new DateOnly(2026, 2, 28), feb[0].PeriodEnd);
    }

    [Fact]
    public void Period_Resolve_CasosBorde()
    {
        Assert.Equal((new DateOnly(2026, 5, 16), new DateOnly(2026, 6, 15)),
            StatementPeriod.Resolve(2026, 6, 15));
        Assert.Equal((new DateOnly(2026, 2, 1), new DateOnly(2026, 2, 28)),
            StatementPeriod.Resolve(2026, 2, 31));
        // Año bisiesto: febrero 2028 tiene 29 días.
        Assert.Equal((new DateOnly(2028, 2, 1), new DateOnly(2028, 2, 29)),
            StatementPeriod.Resolve(2028, 2, 31));
    }

    [Fact]
    public void Generation_NextRunDelay_ApuntaAMedianoche()
    {
        var now = new DateTime(2026, 6, 16, 18, 30, 0, DateTimeKind.Utc);
        Assert.Equal(TimeSpan.FromHours(5.5), StatementGenerationService.NextRunDelay(now));
    }
}

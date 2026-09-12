using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes: quitar cada Where (from/to/category/direction/status/search),
/// quitar Math.Clamp, cambiar orden, quitar RequireAccount.
/// </summary>
public class AccountQueryServiceTests
{
    private static async Task<(TestDb t, int uid, int acc)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "Q", Email = "q@q.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A",
            MaskedNumber = "****1", Currency = "MXN", Balance = 100m,
            Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        await t.Db.SaveChangesAsync();
        var d = new DateOnly(2026, 6, 14);
        t.Db.Transactions.AddRange(
            new Transaction { IdAccount = acc.IdAccount, Date = d, Amount = 10m, Direction = "debit", Category = "super", Description = "Súper centro", Status = "posted", Reference = "A1" },
            new Transaction { IdAccount = acc.IdAccount, Date = d.AddDays(1), Amount = 20m, Direction = "credit", Category = "nomina", Description = "Nómina", Status = "posted", Reference = "B2" },
            new Transaction { IdAccount = acc.IdAccount, Date = d.AddDays(2), Amount = 30m, Direction = "debit", Category = "super", Description = "Oxxo", Status = "pending", Reference = "C3" });
        await t.Db.SaveChangesAsync();
        return (t, u.IdUser, acc.IdAccount);
    }

    [Fact]
    public async Task Transactions_FiltraPorCategoria()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc, null, null, "super", null, null, null, 50);
        Assert.Equal(2, r.Count);
        Assert.All(r, x => Assert.Equal("super", x.Category));
    }

    [Fact]
    public async Task Transactions_FiltraPorRangoFechas()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc, new DateOnly(2026, 6, 15), new DateOnly(2026, 6, 16), null, null, null, null, 50);
        Assert.Equal(2, r.Count);
    }

    [Fact]
    public async Task Transactions_BuscaPorTexto_YRespetaLimite()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc, null, null, null, null, null, "Nómina", 50);
        Assert.Single(r);
        var one = await svc.TransactionsAsync(uid, acc, null, null, null, null, null, null, 1);
        Assert.Single(one); // mata: quitar Take/Clamp
    }

    [Fact]
    public async Task Transactions_CuentaAjena_LanzaNotFound()
    {
        var (t, _, acc) = await ArrangeAsync();
        using var _2 = t;
        var svc = new AccountQueryService(t.Db);
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.TransactionsAsync(9999, acc, null, null, null, null, null, null, 50));
    }

    [Fact]
    public async Task List_SoloDevuelveCuentasPropias()
    {
        var (t, uid, _) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        var other = new User { Name = "O", Email = "o@o.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(other);
        await t.Db.SaveChangesAsync();
        t.Db.Accounts.Add(new Account
        {
            IdUser = other.IdUser, AccountType = "debito", Alias = "X",
            MaskedNumber = "****9", Currency = "MXN", Balance = 1m, Status = "active", CreatedAt = now
        });
        await t.Db.SaveChangesAsync();
        var svc = new AccountQueryService(t.Db);
        var mine = await svc.ListAsync(uid);
        Assert.Single(mine);
    }
}

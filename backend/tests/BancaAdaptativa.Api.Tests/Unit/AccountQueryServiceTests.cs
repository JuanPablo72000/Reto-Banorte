using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.EntityFrameworkCore;

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
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.TransactionsAsync(9999, acc, null, null, null, null, null, null, 50));
        Assert.Equal("ACCOUNT_NOT_FOUND", ex.Message); // mata #869
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

    [Fact] // mata #889/#891: filtro direction
    public async Task Transactions_FiltraPorDirection()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc, null, null, null, "credit", null, null, 50);
        Assert.Single(r);
        Assert.All(r, x => Assert.Equal("credit", x.Direction));
    }

    [Fact] // mata #894/#896: filtro status
    public async Task Transactions_FiltraPorStatus()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc, null, null, null, null, "pending", null, 50);
        Assert.Single(r);
        Assert.All(r, x => Assert.Equal("pending", x.Status));
    }

    [Fact] // mata #872: GetAsync sin cobertura
    public async Task Get_Ok_YAjenoLanza()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _2 = t;
        var svc = new AccountQueryService(t.Db);

        var got = await svc.GetAsync(uid, acc);
        Assert.Equal(acc, got.IdAccount);

        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() => svc.GetAsync(9999, acc));
        Assert.Equal("ACCOUNT_NOT_FOUND", ex.Message);
    }

    [Fact] // mata #905-913: BalancesAsync sin cobertura
    public async Task Balances_ListaYRangoFechas()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var d1 = new DateOnly(2026, 6, 14);
        var d2 = new DateOnly(2026, 6, 15);
        t.Db.DailyBalances.AddRange(
            new DailyBalance { IdAccount = acc, Date = d1, OpeningBalance = 100m, Income = 10m, Expenses = 5m, ClosingBalance = 105m },
            new DailyBalance { IdAccount = acc, Date = d2, OpeningBalance = 105m, Income = 0m, Expenses = 5m, ClosingBalance = 100m });
        await t.Db.SaveChangesAsync();
        var svc = new AccountQueryService(t.Db);

        var all = await svc.BalancesAsync(uid, acc, null, null);
        Assert.Equal(2, all.Count);
        Assert.Equal(d1, all[0].Date); // orden ascendente

        var filtered = await svc.BalancesAsync(uid, acc, d2, d2);
        Assert.Single(filtered);
        Assert.Equal(100m, filtered[0].ClosingBalance);

        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() => svc.BalancesAsync(9999, acc, null, null));
        Assert.Equal("ACCOUNT_NOT_FOUND", ex.Message);
    }

    [Fact] // mata #916: ReconciliationAsync sin cobertura
    public async Task Reconciliation_SoloDevuelvePropias()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        var other = new User { Name = "O", Email = "o@o.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(other);
        await t.Db.SaveChangesAsync();
        var otherAcc = new Account
        {
            IdUser = other.IdUser, AccountType = "debito", Alias = "X",
            MaskedNumber = "****9", Currency = "MXN", Balance = 1m, Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(otherAcc);
        await t.Db.SaveChangesAsync();

        var txs = await t.Db.Transactions.OrderBy(x => x.IdTransaction).Take(2).ToListAsync();
        async Task<int> SeedMatch(int userId, int accountId, int txId, string key)
        {
            var tr = new Transfer
            {
                IdUser = userId, IdOriginAccount = accountId, DestinationAlias = "D",
                DestinationMasked = "****1", Amount = 5m, Currency = "MXN",
                Status = "confirmed", IdempotencyKey = key, ConfirmedAt = now
            };
            t.Db.Transfers.Add(tr);
            await t.Db.SaveChangesAsync();
            t.Db.ReconciliationMatches.Add(new ReconciliationMatch
            {
                IdTransfer = tr.IdTransfer, IdTransaction = txId,
                Status = "matched", MatchScore = 0.9f, MatchedAt = now, Notes = "n"
            });
            await t.Db.SaveChangesAsync();
            return tr.IdTransfer;
        }
        await SeedMatch(uid, acc, txs[0].IdTransaction, "rec-a");
        await SeedMatch(other.IdUser, otherAcc.IdAccount, txs[1].IdTransaction, "rec-b");

        var svc = new AccountQueryService(t.Db);
        var mine = await svc.ReconciliationAsync(uid);
        Assert.Single(mine);
        Assert.Equal("matched", mine[0].Status);
    }
}

using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Reglas críticas OpenCodeInstructions: UTC Kind=Utc, DateOnly, decimal, índices únicos, seed idempotente.
/// Mutantes: quitar converters UTC, quitar IsUnique, quitar guard db.Users.Any.
/// </summary>
public class DataIntegrityTests
{
    [Fact]
    public async Task GuardarDateTime_LeeConKindUtc()
    {
        using var t = new TestDb();
        var u = new User { Name = "U", Email = "u@u.mx", PasswordHash = "x", CreatedAt = TestDb.FixedNow.UtcDateTime };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        t.Db.ChangeTracker.Clear();

        var read = await t.Db.Users.SingleAsync(x => x.Email == "u@u.mx");
        Assert.Equal(DateTimeKind.Utc, read.CreatedAt.Kind);
    }

    [Fact]
    public async Task GuardarDateTimeLocal_LoNormalizaAUtc()
    {
        using var t = new TestDb();
        var local = DateTime.SpecifyKind(new DateTime(2026, 6, 16, 12, 0, 0), DateTimeKind.Local);
        t.Db.Users.Add(new User { Name = "L", Email = "l@l.mx", PasswordHash = "x", CreatedAt = local });
        await t.Db.SaveChangesAsync();
        t.Db.ChangeTracker.Clear();
        var read = await t.Db.Users.SingleAsync(x => x.Email == "l@l.mx");
        Assert.Equal(DateTimeKind.Utc, read.CreatedAt.Kind);
        Assert.Equal(local.ToUniversalTime(), read.CreatedAt);
    }

    [Fact]
    public async Task Dinero_PreservaPrecisionDecimal()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "D", Email = "d@d.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A", MaskedNumber = "****1",
            Currency = "MXN", Balance = 25400.50m, Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        await t.Db.SaveChangesAsync();
        t.Db.ChangeTracker.Clear();
        Assert.Equal(25400.50m, (await t.Db.Accounts.SingleAsync()).Balance);
    }

    [Fact]
    public async Task DailyBalance_IndiceUnico_PorCuentaYFecha()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "B", Email = "b@b.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A", MaskedNumber = "****1",
            Currency = "MXN", Balance = 1m, Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        await t.Db.SaveChangesAsync();
        var day = new DateOnly(2026, 6, 16);
        t.Db.DailyBalances.Add(new DailyBalance
        {
            IdAccount = acc.IdAccount, Date = day, OpeningBalance = 1m, Income = 0m, Expenses = 0m, ClosingBalance = 1m
        });
        await t.Db.SaveChangesAsync();
        t.Db.DailyBalances.Add(new DailyBalance
        {
            IdAccount = acc.IdAccount, Date = day, OpeningBalance = 1m, Income = 0m, Expenses = 0m, ClosingBalance = 1m
        });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }

    [Fact]
    public async Task Transfer_IdempotencyKey_EsUnico()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "K", Email = "k@k.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A", MaskedNumber = "****1",
            Currency = "MXN", Balance = 1m, Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        await t.Db.SaveChangesAsync();
        t.Db.Transfers.Add(new Transfer
        {
            IdUser = u.IdUser, IdOriginAccount = acc.IdAccount, DestinationAlias = "A",
            DestinationMasked = "****1", Amount = 1m, Status = "pending", IdempotencyKey = "same"
        });
        await t.Db.SaveChangesAsync();
        t.Db.Transfers.Add(new Transfer
        {
            IdUser = u.IdUser, IdOriginAccount = acc.IdAccount, DestinationAlias = "B",
            DestinationMasked = "****2", Amount = 2m, Status = "pending", IdempotencyKey = "same"
        });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }

    [Fact]
    public void Seeder_EsIdempotente_NoDuplica()
    {
        using var t = new TestDb();
        DbSeeder.Seed(t.Db, t.Time);
        var users1 = t.Db.Users.Count();
        Assert.Equal(1, users1);
        DbSeeder.Seed(t.Db, t.Time); // segunda corrida no debe insertar
        Assert.Equal(1, t.Db.Users.Count());
        Assert.All(t.Db.Users, u => Assert.Equal(DateTimeKind.Utc, u.CreatedAt.Kind));
    }

    [Fact]
    public void Seeder_CreaGrafoDemo_Completo()
    {
        using var t = new TestDb();
        DbSeeder.Seed(t.Db, t.Time);
        Assert.NotEmpty(t.Db.Accounts.ToList());
        Assert.NotEmpty(t.Db.Transactions.ToList());
        Assert.NotEmpty(t.Db.Transfers.ToList());
        Assert.NotEmpty(t.Db.Sessions.ToList());
        Assert.NotEmpty(t.Db.AuditLogs.ToList());
        var transfer = t.Db.Transfers.Single();
        Assert.Equal("pending", transfer.Status); // mata: seed con confirmed
        Assert.Null(transfer.ConfirmedAt);
    }
}

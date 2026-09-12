using BancaAdaptativa.Api.Dtos.Transfers;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Filtros de búsqueda (from/to, categorías, cuentas, estados):
/// cada Where agregado debe estar cubierto para que la IA pueda filtrar.
/// </summary>
public class QueryFiltersTests
{
    private static async Task<(TestDb t, int uid, int acc1, int acc2)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "F", Email = "f@f.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        var a1 = new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "Nómina",
            MaskedNumber = "****1", Currency = "MXN", Balance = 100m, Status = "active", CreatedAt = now
        };
        var a2 = new Account
        {
            IdUser = u.IdUser, AccountType = "credito", Alias = "TC",
            MaskedNumber = "****2", Currency = "MXN", Balance = 0m, Status = "blocked", CreatedAt = now
        };
        t.Db.Accounts.AddRange(a1, a2);
        var super = new ExpenseCategory { Name = "Supermercados", Code = "supermarket", Icon = "cart", IsDefault = true, SortOrder = 6 };
        t.Db.ExpenseCategories.Add(super);
        await t.Db.SaveChangesAsync();
        var d = new DateOnly(2026, 6, 14);
        t.Db.Transactions.AddRange(
            new Transaction { IdAccount = a1.IdAccount, Date = d, Amount = 10m, Direction = "debit", Category = "super", Description = "Súper", Status = "posted", Reference = "A1", IdExpenseCategory = super.IdCategory },
            new Transaction { IdAccount = a2.IdAccount, Date = d, Amount = 20m, Direction = "debit", Category = "super", Description = "Súper TC", Status = "posted", Reference = "A2" });
        var other = new User { Name = "O", Email = "o@o.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(other);
        await t.Db.SaveChangesAsync();
        var oa = new Account
        {
            IdUser = other.IdUser, AccountType = "debito", Alias = "OA",
            MaskedNumber = "****9", Currency = "MXN", Balance = 1m, Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(oa);
        await t.Db.SaveChangesAsync();
        t.Db.Transactions.Add(
            new Transaction { IdAccount = oa.IdAccount, Date = d, Amount = 99m, Direction = "debit", Category = "super", Description = "Ajeno", Status = "posted", Reference = "Z9" });
        await t.Db.SaveChangesAsync();
        return (t, u.IdUser, a1.IdAccount, a2.IdAccount);
    }

    [Fact]
    public async Task Accounts_FiltraPorStatusYTipo()
    {
        var (t, uid, _, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new AccountQueryService(t.Db);
        Assert.Equal(2, (await svc.ListAsync(uid)).Count);
        Assert.Single(await svc.ListAsync(uid, "active"));
        Assert.Single(await svc.ListAsync(uid, null, "credito"));
        Assert.Empty(await svc.ListAsync(uid, "active", "credito"));
    }

    [Fact]
    public async Task Transactions_FiltraPorExpenseCategory()
    {
        var (t, uid, acc1, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new AccountQueryService(t.Db);
        var r = await svc.TransactionsAsync(uid, acc1, null, null, null, null, null, null, 50, "supermarket");
        Assert.Single(r);
        Assert.Empty(await svc.TransactionsAsync(uid, acc1, null, null, null, null, null, null, 50, "transport"));
    }

    [Fact]
    public async Task AllTransactions_BuscaGlobal_YRespetaPropiedad()
    {
        var (t, uid, acc1, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new AccountQueryService(t.Db);
        var all = await svc.AllTransactionsAsync(uid, null, null, null, null, null, null, null, null, 50);
        Assert.Equal(2, all.Count); // solo mías, no la del otro usuario
        Assert.All(all, x => Assert.NotEqual(99m, x.Amount));
        var scoped = await svc.AllTransactionsAsync(uid, acc1, null, null, null, null, null, null, null, 50);
        Assert.Single(scoped);
        Assert.Equal(acc1, scoped[0].IdAccount);
        var otherAcc = await t.Db.Accounts.AsNoTracking().FirstAsync(a => a.Alias == "OA");
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.AllTransactionsAsync(uid, otherAcc.IdAccount, null, null, null, null, null, null, null, 50));
    }

    [Fact]
    public async Task Reconciliation_FiltraPorStatus()
    {
        var (t, uid, acc1, _) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        var tx = await t.Db.Transactions.FirstAsync(x => x.IdAccount == acc1);
        var tr = new Transfer
        {
            IdUser = uid, IdOriginAccount = acc1, DestinationAlias = "X", DestinationMasked = "****0",
            Amount = 5m, Currency = "MXN", Concept = "", Status = "confirmed",
            IdempotencyKey = Guid.NewGuid().ToString(), CreatedAt = now, ConfirmedAt = now
        };
        t.Db.Transfers.Add(tr);
        await t.Db.SaveChangesAsync();
        t.Db.ReconciliationMatches.Add(new ReconciliationMatch
        {
            IdTransfer = tr.IdTransfer, IdTransaction = tx.IdTransaction,
            Status = "matched", MatchScore = 0.9f, MatchedAt = now, Notes = ""
        });
        await t.Db.SaveChangesAsync();
        var svc = new AccountQueryService(t.Db);
        Assert.Single(await svc.ReconciliationAsync(uid));
        Assert.Single(await svc.ReconciliationAsync(uid, "matched"));
        Assert.Empty(await svc.ReconciliationAsync(uid, "pending"));
    }

    [Fact]
    public async Task Statements_FiltraPorStatus()
    {
        var (t, uid, acc1, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new StatementService(t.Db, t.Time, new BudgetService(t.Db, t.Time));
        await svc.GenerateAsync(uid, acc1, 2026, 6, 15);
        await svc.GenerateAsync(uid, acc1, 2026, 7, 15);
        var first = (await svc.ListAsync(uid, acc1, null, null)).OrderBy(s => s.PeriodStart).First();
        var entity = await t.Db.Statements.FindAsync(first.IdStatement);
        entity!.Status = "archived";
        await t.Db.SaveChangesAsync();
        Assert.Equal(2, (await svc.ListAsync(uid, acc1, null, null)).Count);
        Assert.Single(await svc.ListAsync(uid, acc1, null, null, "archived"));
        Assert.Single(await svc.ListAsync(uid, acc1, null, null, "generated"));
    }

    [Fact]
    public async Task Budgets_FiltraPorCategoriaYStatus()
    {
        var (t, uid, _, _) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        var cat = await t.Db.ExpenseCategories.FirstAsync(c => c.Code == "supermarket");
        t.Db.ExpenseCategories.Add(new ExpenseCategory { Name = "Transporte", Code = "transport", Icon = "t", IsDefault = true, SortOrder = 7 });
        await t.Db.SaveChangesAsync();
        var trans = await t.Db.ExpenseCategories.FirstAsync(c => c.Code == "transport");
        t.Db.Budgets.AddRange(
            new Budget { IdUser = uid, IdExpenseCategory = cat.IdCategory, Month = 6, Year = 2026, AmountLimit = 100m, CurrentSpent = 10m, StartDate = now, EndDate = now, Status = "active", CreatedAt = now, UpdatedAt = now },
            new Budget { IdUser = uid, IdExpenseCategory = trans.IdCategory, Month = 6, Year = 2026, AmountLimit = 50m, CurrentSpent = 60m, StartDate = now, EndDate = now, Status = "exceeded", CreatedAt = now, UpdatedAt = now });
        await t.Db.SaveChangesAsync();
        var svc = new BudgetService(t.Db, t.Time);
        Assert.Equal(2, (await svc.MonthlySummaryAsync(uid, 2026, 6)).Budgets.Count);
        Assert.Single((await svc.MonthlySummaryAsync(uid, 2026, 6, "supermarket")).Budgets);
        Assert.Single((await svc.MonthlySummaryAsync(uid, 2026, 6, null, "exceeded")).Budgets);
    }

    [Fact]
    public async Task SavingsGoals_FiltraPorStatus()
    {
        var (t, uid, _, _) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        t.Db.SavingsGoals.AddRange(
            new SavingsGoal { IdUser = uid, Name = "A", TargetAmount = 100m, CurrentAmount = 10m, TargetDate = now, Status = "active", CreatedAt = now, UpdatedAt = now },
            new SavingsGoal { IdUser = uid, Name = "B", TargetAmount = 100m, CurrentAmount = 100m, TargetDate = now, Status = "completed", CreatedAt = now, UpdatedAt = now });
        await t.Db.SaveChangesAsync();
        var svc = new SavingsGoalService(t.Db, t.Time);
        Assert.Equal(2, (await svc.ListAsync(uid)).Count);
        Assert.Single(await svc.ListAsync(uid, "completed"));
    }

    [Fact]
    public async Task CreditCards_FiltraPorStatus_YStatementsPorMes()
    {
        var (t, uid, _, _) = await ArrangeAsync();
        using var _2 = t;
        var now = TestDb.FixedNow.UtcDateTime;
        t.Db.CreditCards.AddRange(
            new CreditCard { IdUser = uid, CardNumberMasked = "****1", CardType = "Visa", CreditLimit = 1000m, AvailableCredit = 900m, InterestRate = 20m, StatementCutOffDay = 15, PaymentDueDay = 5, Status = "active", CreatedAt = now },
            new CreditCard { IdUser = uid, CardNumberMasked = "****2", CardType = "MC", CreditLimit = 500m, AvailableCredit = 500m, InterestRate = 20m, StatementCutOffDay = 15, PaymentDueDay = 5, Status = "blocked", CreatedAt = now });
        await t.Db.SaveChangesAsync();
        var svc = new CreditCardService(t.Db, t.Time);
        Assert.Equal(2, (await svc.ListAsync(uid)).Count);
        Assert.Single(await svc.ListAsync(uid, "blocked"));
        var card = (await svc.ListAsync(uid, "active")).Single();
        await svc.GenerateStatementAsync(uid, card.IdCreditCard, 2026, 6, 100m, 0m);
        await svc.GenerateStatementAsync(uid, card.IdCreditCard, 2026, 7, 50m, 0m);
        Assert.Equal(2, (await svc.StatementsAsync(uid, card.IdCreditCard)).Count);
        Assert.Single(await svc.StatementsAsync(uid, card.IdCreditCard, 2026, 6));
    }

    [Fact]
    public async Task Transfers_ListaConFiltrosDeEstadoFechaYCuenta()
    {
        var (t, uid, acc1, acc2) = await ArrangeAsync();
        using var _2 = t;
        var svc = new TransferService(t.Db, t.Time);
        await svc.CreateAsync(uid, new CreateTransferRequest(acc1, "Mamá", "****1", 10m));
        await svc.CreateAsync(uid, new CreateTransferRequest(acc1, "Papá", "****2", 20m));
        var other = await svc.CreateAsync(uid, new CreateTransferRequest(acc2, "TC", "****3", 30m));
        await svc.ConfirmAsync(uid, other.IdTransfer, "app");
        var now = TestDb.FixedNow;
        Assert.Equal(3, (await svc.ListAsync(uid)).Count);
        Assert.Equal(2, (await svc.ListAsync(uid, "pending")).Count);
        Assert.Single(await svc.ListAsync(uid, "confirmed"));
        Assert.Single(await svc.ListAsync(uid, null, acc2));
        Assert.Equal(3, (await svc.ListAsync(uid, null, null, now.AddHours(-1).UtcDateTime, now.AddHours(1).UtcDateTime)).Count);
        Assert.Empty(await svc.ListAsync(uid, null, null, now.AddHours(1).UtcDateTime, null));
        Assert.Single(await svc.ListAsync(uid, null, null, null, null, 1));
    }
}

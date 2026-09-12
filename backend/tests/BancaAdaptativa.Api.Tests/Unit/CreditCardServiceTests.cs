using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Unit;

public class CreditCardServiceTests
{
    private static async Task<(TestDb t, int uid, int card)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "C", Email = "c@c.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        // Ancla contable requerida por los statements de tarjeta.
        t.Db.Accounts.Add(new Account
        {
            IdUser = u.IdUser, AccountType = "debito", Alias = "A",
            MaskedNumber = "****1", Currency = "MXN", Balance = 1000m,
            Status = "active", CreatedAt = now
        });
        await t.Db.SaveChangesAsync();
        var svc = new CreditCardService(t.Db, t.Time);
        var card = await svc.CreateAsync(u.IdUser, new CreateCreditCardRequest(
            "****5678", "Visa", 30000m, 24m, 15, 5));
        return (t, u.IdUser, card.IdCreditCard);
    }

    [Fact]
    public async Task Generate_CalculaInteresMinimoYDisponible()
    {
        var (t, uid, card) = await ArrangeAsync();
        using var _ = t;
        var svc = new CreditCardService(t.Db, t.Time);

        var s = await svc.GenerateStatementAsync(uid, card, 2026, 6, totalPurchases: 3250.50m, totalPayments: 1000m);

        Assert.Equal(0m, s.PreviousBalance);
        Assert.Equal(0m, s.InterestCharges); // sin saldo previo no hay interés
        Assert.Equal(112.53m, s.MinimumPayment); // 5% de 2250.50
        Assert.Equal(new DateOnly(2026, 6, 5), s.PaymentDueDate);
        Assert.Equal(27749.50m, s.AvailableCredit);

        var list = await svc.StatementsAsync(uid, card);
        Assert.Single(list);
    }

    [Fact]
    public async Task Generate_SegundoMes_CobraInteresSobreImpago()
    {
        var (t, uid, card) = await ArrangeAsync();
        using var _ = t;
        var svc = new CreditCardService(t.Db, t.Time);
        await svc.GenerateStatementAsync(uid, card, 2026, 6, 3250.50m, 1000m);

        // Julio: impago de 2250.50 -> interés 2250.50 * 0.24/12 = 45.01
        var july = await svc.GenerateStatementAsync(uid, card, 2026, 7, 0m, 0m);
        Assert.Equal(2250.50m, july.PreviousBalance);
        Assert.Equal(45.01m, july.InterestCharges);
    }

    [Fact]
    public async Task Generate_EsIdempotente()
    {
        var (t, uid, card) = await ArrangeAsync();
        using var _ = t;
        var svc = new CreditCardService(t.Db, t.Time);
        var a = await svc.GenerateStatementAsync(uid, card, 2026, 6, 100m, 0m);
        var b = await svc.GenerateStatementAsync(uid, card, 2026, 6, 999m, 999m);
        Assert.Equal(a.IdCreditCardStatement, b.IdCreditCardStatement);
    }

    [Fact]
    public async Task Pay_AumentaDisponible_YRegistraAuditoria()
    {
        var (t, uid, card) = await ArrangeAsync();
        using var _ = t;
        var svc = new CreditCardService(t.Db, t.Time);
        await svc.GenerateStatementAsync(uid, card, 2026, 6, 3250.50m, 1000m);

        var paid = await svc.PayAsync(uid, card, 500m);
        Assert.Equal(28249.50m, paid.AvailableCredit);
        Assert.Contains(t.Db.AuditLogs, a => a.Action == "credit-card.pay");
    }

    [Fact]
    public async Task Generate_TarjetaAjena_LanzaNotFound()
    {
        var (t, _, card) = await ArrangeAsync();
        using var _2 = t;
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            new CreditCardService(t.Db, t.Time).GenerateStatementAsync(9999, card, 2026, 6, 0m, 0m));
        Assert.Equal("CARD_NOT_FOUND", ex.Message);
    }
}

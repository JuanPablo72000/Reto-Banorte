using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Services;

public interface ICreditCardService
{
    Task<CreditCardResponse> CreateAsync(int idUser, CreateCreditCardRequest req, CancellationToken ct = default);
    Task<IReadOnlyList<CreditCardResponse>> ListAsync(int idUser, string? status = null, CancellationToken ct = default);
    Task<CreditCardStatementResponse> GenerateStatementAsync(int idUser, int cardId, int year, int month, decimal totalPurchases, decimal totalPayments, CancellationToken ct = default);
    Task<IReadOnlyList<CreditCardStatementResponse>> StatementsAsync(int idUser, int cardId, int? year = null, int? month = null, CancellationToken ct = default);
    Task<CreditCardResponse> PayAsync(int idUser, int cardId, decimal amount, CancellationToken ct = default);
}

public class CreditCardService(AppDbContext db, TimeProvider timeProvider) : ICreditCardService
{
    private static CreditCardResponse Map(CreditCard c) =>
        new(c.IdCreditCard, c.CardNumberMasked, c.CardType, c.CreditLimit, c.AvailableCredit,
            c.InterestRate, c.StatementCutOffDay, c.PaymentDueDay, c.Status, c.CreatedAt);

    private static CreditCardStatementResponse MapStmt(CreditCardStatement s, DateOnly start, DateOnly end) =>
        new(s.IdCreditCardStatement, s.IdCreditCard, s.IdStatement, start, end,
            s.PreviousBalance, s.TotalPayments, s.TotalCredits, s.TotalPurchases,
            s.InterestCharges, s.MinimumPayment, s.PaymentDueDate, s.AvailableCredit,
            s.Status, s.GeneratedAt);

    private async Task<CreditCard> RequireCardAsync(int idUser, int cardId, CancellationToken ct)
    {
        var c = await db.CreditCards.FirstOrDefaultAsync(x => x.IdCreditCard == cardId && x.IdUser == idUser, ct);
        return c ?? throw new KeyNotFoundException("CARD_NOT_FOUND");
    }

    public async Task<CreditCardResponse> CreateAsync(int idUser, CreateCreditCardRequest req, CancellationToken ct = default)
    {
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var c = new CreditCard
        {
            IdUser = idUser,
            CardNumberMasked = req.CardNumberMasked.Trim(),
            CardType = string.IsNullOrWhiteSpace(req.CardType) ? "Visa" : req.CardType.Trim(),
            CreditLimit = req.CreditLimit,
            AvailableCredit = req.CreditLimit,
            InterestRate = req.InterestRate,
            StatementCutOffDay = Math.Clamp(req.StatementCutOffDay, 1, 31),
            PaymentDueDay = Math.Clamp(req.PaymentDueDay, 1, 31),
            Status = "active",
            CreatedAt = nowUtc
        };
        db.CreditCards.Add(c);
        await db.SaveChangesAsync(ct);
        return Map(c);
    }

    public async Task<IReadOnlyList<CreditCardResponse>> ListAsync(int idUser, string? status = null, CancellationToken ct = default)
    {
        var q = db.CreditCards.AsNoTracking().Where(c => c.IdUser == idUser);
        if (!string.IsNullOrWhiteSpace(status)) q = q.Where(c => c.Status == status);
        return await q.OrderBy(c => c.IdCreditCard)
            .Select(c => new CreditCardResponse(c.IdCreditCard, c.CardNumberMasked, c.CardType,
                c.CreditLimit, c.AvailableCredit, c.InterestRate,
                c.StatementCutOffDay, c.PaymentDueDay, c.Status, c.CreatedAt))
            .ToListAsync(ct);
    }

    public async Task<CreditCardStatementResponse> GenerateStatementAsync(int idUser, int cardId, int year, int month, decimal totalPurchases, decimal totalPayments, CancellationToken ct = default)
    {
        var card = await RequireCardAsync(idUser, cardId, ct);
        if (month < 1 || month > 12) throw new ArgumentOutOfRangeException(nameof(month), "MONTH_OUT_OF_RANGE");
        if (totalPurchases < 0 || totalPayments < 0) throw new ArgumentOutOfRangeException("AMOUNTS_MUST_BE_NON_NEGATIVE");

        var (start, end) = StatementPeriod.Resolve(year, month, card.StatementCutOffDay);

        var existing = await db.CreditCardStatements.AsNoTracking()
            .Include(s => s.Statement)
            .FirstOrDefaultAsync(s => s.IdCreditCard == cardId
                && s.Statement.PeriodStart == start, ct);
        if (existing is not null) return MapStmt(existing, existing.Statement.PeriodStart, existing.Statement.PeriodEnd);

        var prevBalance = await db.CreditCardStatements.AsNoTracking()
            .Include(s => s.Statement)
            .Where(s => s.IdCreditCard == cardId && s.Statement.PeriodEnd < start)
            .OrderByDescending(s => s.Statement.PeriodEnd)
            .Select(s => (decimal?)(s.PreviousBalance + s.TotalPurchases + s.InterestCharges - s.TotalPayments))
            .FirstOrDefaultAsync(ct) ?? 0m;

        var unpaid = Math.Max(0, prevBalance - totalPayments);
        var interest = Math.Round(unpaid * (card.InterestRate / 100m / 12m), 2, MidpointRounding.AwayFromZero);
        var newBalance = prevBalance + totalPurchases + interest - totalPayments;
        var minimum = Math.Round(Math.Max(25m, Math.Max(0, newBalance) * 0.05m), 2, MidpointRounding.AwayFromZero);
        var dueDay = Math.Min(card.PaymentDueDay, DateTime.DaysInMonth(end.Year, end.Month));
        var dueDate = new DateOnly(end.Year, end.Month, dueDay);
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;

        // El statement base reutiliza la tabla Statements con AccountType = "credito".
        // Se liga a la primera cuenta del usuario como contenedor contable.
        var anchor = await db.Accounts.AsNoTracking()
            .Where(a => a.IdUser == idUser).OrderBy(a => a.IdAccount)
            .FirstOrDefaultAsync(ct) ?? throw new KeyNotFoundException("ACCOUNT_NOT_FOUND");

        var stmt = new Statement
        {
            IdAccount = anchor.IdAccount,
            CutOffDay = card.StatementCutOffDay,
            PeriodStart = start,
            PeriodEnd = end,
            OpeningBalance = prevBalance,
            ClosingBalance = newBalance,
            TotalCredits = totalPayments,
            TotalDebits = totalPurchases + interest,
            TransactionCount = 0,
            AccountType = "credito",
            Status = "generated",
            GeneratedAt = nowUtc
        };
        db.Statements.Add(stmt);
        await db.SaveChangesAsync(ct);

        var ccs = new CreditCardStatement
        {
            IdCreditCard = cardId,
            IdStatement = stmt.IdStatement,
            PreviousBalance = prevBalance,
            TotalPayments = totalPayments,
            TotalCredits = totalPayments,
            TotalPurchases = totalPurchases,
            InterestCharges = interest,
            MinimumPayment = minimum,
            PaymentDueDate = dueDate,
            AvailableCredit = card.CreditLimit - Math.Max(0, newBalance),
            Status = "generated",
            GeneratedAt = nowUtc
        };
        db.CreditCardStatements.Add(ccs);
        card.AvailableCredit = ccs.AvailableCredit;
        await db.SaveChangesAsync(ct);
        return MapStmt(ccs, start, end);
    }

    public async Task<IReadOnlyList<CreditCardStatementResponse>> StatementsAsync(int idUser, int cardId, int? year = null, int? month = null, CancellationToken ct = default)
    {
        await RequireCardAsync(idUser, cardId, ct);
        var q = db.CreditCardStatements.AsNoTracking()
            .Include(s => s.Statement)
            .Where(s => s.IdCreditCard == cardId);
        if (year.HasValue) q = q.Where(s => s.Statement.PeriodEnd.Year == year.Value);
        if (month.HasValue) q = q.Where(s => s.Statement.PeriodEnd.Month == month.Value);
        return await q.OrderByDescending(s => s.Statement.PeriodEnd)
            .Select(s => new CreditCardStatementResponse(s.IdCreditCardStatement, s.IdCreditCard, s.IdStatement,
                s.Statement.PeriodStart, s.Statement.PeriodEnd, s.PreviousBalance, s.TotalPayments,
                s.TotalCredits, s.TotalPurchases, s.InterestCharges, s.MinimumPayment,
                s.PaymentDueDate, s.AvailableCredit, s.Status, s.GeneratedAt))
            .ToListAsync(ct);
    }

    public async Task<CreditCardResponse> PayAsync(int idUser, int cardId, decimal amount, CancellationToken ct = default)
    {
        if (amount <= 0) throw new ArgumentOutOfRangeException(nameof(amount), "AMOUNT_MUST_BE_POSITIVE");
        var card = await RequireCardAsync(idUser, cardId, ct);
        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        card.AvailableCredit = Math.Min(card.CreditLimit, card.AvailableCredit + amount);
        db.AuditLogs.Add(new AuditLog
        {
            IdUser = idUser,
            Action = "credit-card.pay",
            Resource = $"card:{card.IdCreditCard}",
            Result = "ok",
            RiskLevel = "low",
            RedactedPayload = $"amount={amount} card={card.CardNumberMasked}",
            CreatedAt = nowUtc
        });
        await db.SaveChangesAsync(ct);
        return Map(card);
    }
}

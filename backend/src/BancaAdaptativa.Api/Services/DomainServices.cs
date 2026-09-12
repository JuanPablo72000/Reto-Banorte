using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Accounts;
using BancaAdaptativa.Api.Dtos.Preferences;
using BancaAdaptativa.Api.Dtos.Reconciliation;
using BancaAdaptativa.Api.Dtos.Transactions;
using BancaAdaptativa.Api.Dtos.Transfers;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;

namespace BancaAdaptativa.Api.Services;

public interface IPreferenceService
{
    Task<AccessibilityPreferenceResponse> GetAsync(int idUser, CancellationToken ct = default);
    Task<AccessibilityPreferenceResponse> UpdateAsync(int idUser, Dtos.Preferences.UpdatePreferencesRequest req, CancellationToken ct = default);
}

public class PreferenceService(AppDbContext db, TimeProvider timeProvider) : IPreferenceService
{
    public async Task<AccessibilityPreferenceResponse> GetAsync(int idUser, CancellationToken ct = default)
    {
        var p = await db.AccessibilityPreferences.AsNoTracking().FirstOrDefaultAsync(x => x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("PREFERENCES_NOT_FOUND");
        return new(p.IdPreference, p.FontScale, p.HighContrast, p.DarkMode, p.ReducedMotion, p.LargeTargets, p.PlainLanguage, p.UpdatedAt);
    }

    public async Task<AccessibilityPreferenceResponse> UpdateAsync(int idUser, Dtos.Preferences.UpdatePreferencesRequest req, CancellationToken ct = default)
    {
        var p = await db.AccessibilityPreferences.FirstOrDefaultAsync(x => x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("PREFERENCES_NOT_FOUND");
        if (req.FontScale.HasValue) p.FontScale = req.FontScale.Value;
        if (req.HighContrast.HasValue) p.HighContrast = req.HighContrast.Value;
        if (req.DarkMode.HasValue) p.DarkMode = req.DarkMode.Value;
        if (req.ReducedMotion.HasValue) p.ReducedMotion = req.ReducedMotion.Value;
        if (req.LargeTargets.HasValue) p.LargeTargets = req.LargeTargets.Value;
        if (req.PlainLanguage.HasValue) p.PlainLanguage = req.PlainLanguage.Value;
        p.UpdatedAt = timeProvider.GetUtcNow().UtcDateTime;
        await db.SaveChangesAsync(ct);
        return new(p.IdPreference, p.FontScale, p.HighContrast, p.DarkMode, p.ReducedMotion, p.LargeTargets, p.PlainLanguage, p.UpdatedAt);
    }
}

public interface IAccountQueryService
{
    Task<IReadOnlyList<AccountResponse>> ListAsync(int idUser, CancellationToken ct = default);
    Task<AccountResponse> GetAsync(int idUser, int accountId, CancellationToken ct = default);
    Task<IReadOnlyList<TransactionResponse>> TransactionsAsync(int idUser, int accountId, DateOnly? from, DateOnly? to, string? category, string? direction, string? status, string? search, int limit, CancellationToken ct = default);
    Task<IReadOnlyList<DailyBalanceResponse>> BalancesAsync(int idUser, int accountId, DateOnly? from, DateOnly? to, CancellationToken ct = default);
    Task<IReadOnlyList<ReconciliationResponse>> ReconciliationAsync(int idUser, CancellationToken ct = default);
}

public class AccountQueryService(AppDbContext db) : IAccountQueryService
{
    private async Task<Account> RequireAccountAsync(int idUser, int accountId, CancellationToken ct)
    {
        var a = await db.Accounts.AsNoTracking().FirstOrDefaultAsync(x => x.IdAccount == accountId && x.IdUser == idUser, ct);
        return a ?? throw new KeyNotFoundException("ACCOUNT_NOT_FOUND");
    }

    public async Task<IReadOnlyList<AccountResponse>> ListAsync(int idUser, CancellationToken ct = default) =>
        await db.Accounts.AsNoTracking().Where(a => a.IdUser == idUser).OrderBy(a => a.IdAccount)
            .Select(a => new AccountResponse(a.IdAccount, a.AccountType, a.Alias, a.MaskedNumber, a.Currency, a.Balance, a.Status, a.CreatedAt))
            .ToListAsync(ct);

    public async Task<AccountResponse> GetAsync(int idUser, int accountId, CancellationToken ct = default)
    {
        var a = await RequireAccountAsync(idUser, accountId, ct);
        return new(a.IdAccount, a.AccountType, a.Alias, a.MaskedNumber, a.Currency, a.Balance, a.Status, a.CreatedAt);
    }

    public async Task<IReadOnlyList<TransactionResponse>> TransactionsAsync(int idUser, int accountId, DateOnly? from, DateOnly? to, string? category, string? direction, string? status, string? search, int limit, CancellationToken ct = default)
    {
        await RequireAccountAsync(idUser, accountId, ct);
        limit = Math.Clamp(limit, 1, 100);
        var q = db.Transactions.AsNoTracking().Where(t => t.IdAccount == accountId);
        if (from.HasValue) q = q.Where(t => t.Date >= from.Value);
        if (to.HasValue) q = q.Where(t => t.Date <= to.Value);
        if (!string.IsNullOrWhiteSpace(category)) q = q.Where(t => t.Category == category);
        if (!string.IsNullOrWhiteSpace(direction)) q = q.Where(t => t.Direction == direction);
        if (!string.IsNullOrWhiteSpace(status)) q = q.Where(t => t.Status == status);
        if (!string.IsNullOrWhiteSpace(search)) q = q.Where(t => t.Description.Contains(search) || t.Reference.Contains(search));
        return await q.OrderByDescending(t => t.Date).ThenByDescending(t => t.IdTransaction).Take(limit)
            .Select(t => new TransactionResponse(t.IdTransaction, t.Date, t.Amount, t.Direction, t.Category, t.Description, t.Status, t.Reference, t.IdExpenseCategory))
            .ToListAsync(ct);
    }

    public async Task<IReadOnlyList<DailyBalanceResponse>> BalancesAsync(int idUser, int accountId, DateOnly? from, DateOnly? to, CancellationToken ct = default)
    {
        await RequireAccountAsync(idUser, accountId, ct);
        var q = db.DailyBalances.AsNoTracking().Where(d => d.IdAccount == accountId);
        if (from.HasValue) q = q.Where(d => d.Date >= from.Value);
        if (to.HasValue) q = q.Where(d => d.Date <= to.Value);
        return await q.OrderBy(d => d.Date)
            .Select(d => new DailyBalanceResponse(d.IdBalance, d.Date, d.OpeningBalance, d.Income, d.Expenses, d.ClosingBalance))
            .ToListAsync(ct);
    }

    public async Task<IReadOnlyList<ReconciliationResponse>> ReconciliationAsync(int idUser, CancellationToken ct = default) =>
        await db.ReconciliationMatches.AsNoTracking()
            .Where(r => r.Transfer.IdUser == idUser)
            .OrderByDescending(r => r.IdMatch)
            .Select(r => new ReconciliationResponse(r.IdMatch, r.IdTransfer, r.IdTransaction, r.Status, r.MatchScore, r.MatchedAt, r.Notes))
            .ToListAsync(ct);
}

public interface ITransferService
{
    Task<TransferResponse> CreateAsync(int idUser, CreateTransferRequest req, CancellationToken ct = default);
    Task<TransferResponse> GetAsync(int idUser, int transferId, CancellationToken ct = default);
    Task<(TransferResponse Transfer, TransferConfirmationResponse Confirmation)> ConfirmAsync(int idUser, int transferId, string method, CancellationToken ct = default);
}

public class TransferService(AppDbContext db, TimeProvider timeProvider) : ITransferService
{
    private static TransferResponse Map(Transfer t) =>
        new(t.IdTransfer, t.IdOriginAccount, t.DestinationAlias, t.DestinationMasked, t.Amount, t.Currency, t.Concept, t.Status, t.IdempotencyKey, t.ConfirmedAt);

    public async Task<TransferResponse> CreateAsync(int idUser, CreateTransferRequest req, CancellationToken ct = default)
    {
        var key = string.IsNullOrWhiteSpace(req.IdempotencyKey) ? Guid.NewGuid().ToString() : req.IdempotencyKey.Trim();
        var existing = await db.Transfers.AsNoTracking().FirstOrDefaultAsync(t => t.IdempotencyKey == key, ct);
        if (existing is not null) return Map(existing);

        var owns = await db.Accounts.AnyAsync(a => a.IdAccount == req.IdOriginAccount && a.IdUser == idUser, ct);
        if (!owns) throw new KeyNotFoundException("ORIGIN_ACCOUNT_NOT_FOUND");

        var t = new Transfer
        {
            IdUser = idUser,
            IdOriginAccount = req.IdOriginAccount,
            DestinationAlias = req.DestinationAlias.Trim(),
            DestinationMasked = req.DestinationMasked.Trim(),
            Amount = req.Amount,
            Currency = string.IsNullOrWhiteSpace(req.Currency) ? "MXN" : req.Currency.Trim().ToUpperInvariant(),
            Concept = req.Concept ?? string.Empty,
            Status = "pending",
            IdempotencyKey = key,
            ConfirmedAt = null
        };
        db.Transfers.Add(t);
        try { await db.SaveChangesAsync(ct); }
        catch (DbUpdateException) // carrera de idempotencia: devuelve el existente
        {
            var dup = await db.Transfers.AsNoTracking().FirstAsync(x => x.IdempotencyKey == key, ct);
            return Map(dup);
        }
        return Map(t);
    }

    public async Task<TransferResponse> GetAsync(int idUser, int transferId, CancellationToken ct = default)
    {
        var t = await db.Transfers.AsNoTracking().FirstOrDefaultAsync(x => x.IdTransfer == transferId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("TRANSFER_NOT_FOUND");
        return Map(t);
    }

    public async Task<(TransferResponse Transfer, TransferConfirmationResponse Confirmation)> ConfirmAsync(int idUser, int transferId, string method, CancellationToken ct = default)
    {
        var t = await db.Transfers.Include(x => x.OriginAccount).FirstOrDefaultAsync(x => x.IdTransfer == transferId && x.IdUser == idUser, ct)
            ?? throw new KeyNotFoundException("TRANSFER_NOT_FOUND");
        if (t.Status != "pending") throw new InvalidOperationException("TRANSFER_NOT_PENDING");

        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        t.Status = "confirmed";
        t.ConfirmedAt = nowUtc;

        var confirmation = new TransferConfirmation
        {
            IdTransfer = t.IdTransfer,
            Method = string.IsNullOrWhiteSpace(method) ? "app" : method,
            Status = "confirmed",
            ConfirmedAt = nowUtc
        };
        db.TransferConfirmations.Add(confirmation);

        db.AuditLogs.Add(new AuditLog
        {
            IdUser = idUser,
            Action = "transfer.confirm",
            Resource = $"transfer:{t.IdTransfer}",
            Result = "ok",
            RiskLevel = t.Amount > 10000 ? "medium" : "low",
            RedactedPayload = $"amount={t.Amount} dest={t.DestinationMasked}",
            CreatedAt = nowUtc
        });

        await db.SaveChangesAsync(ct);
        return (Map(t), new(confirmation.IdConfirmation, confirmation.Method, confirmation.Status, confirmation.ConfirmedAt));
    }
}

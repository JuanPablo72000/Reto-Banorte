using BancaAdaptativa.Api.Data;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace BancaAdaptativa.Api.Services;

/// <summary>
/// Trigger diario: genera el estado de cuenta del periodo recién cerrado para
/// cada cuenta cuyo día de corte coincide con el día de negocio, más los
/// statements de tarjetas de crédito (base, sin movimientos del periodo).
/// Febrero y meses cortos se manejan vía <see cref="StatementPeriod.Resolve"/>.
/// </summary>
public class StatementGenerationService(
    IServiceScopeFactory scopes,
    TimeProvider timeProvider,
    ILogger<StatementGenerationService> logger) : BackgroundService
{
    public static TimeSpan NextRunDelay(DateTime utcNow)
    {
        var nextMidnight = utcNow.Date.AddDays(1);
        return nextMidnight - utcNow;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                await RunOnceAsync(stoppingToken);
            }
            catch (Exception ex) when (!stoppingToken.IsCancellationRequested)
            {
                logger.LogError(ex, "Error generando estados de cuenta automáticos");
            }
            var delay = NextRunDelay(timeProvider.GetUtcNow().UtcDateTime);
            try { await Task.Delay(delay, stoppingToken); }
            catch (TaskCanceledException) { break; }
        }
    }

    public async Task<int> RunOnceAsync(CancellationToken ct = default)
    {
        using var scope = scopes.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var statements = scope.ServiceProvider.GetRequiredService<IStatementService>();
        var cards = scope.ServiceProvider.GetRequiredService<ICreditCardService>();
        var clock = scope.ServiceProvider.GetRequiredService<IBusinessClock>();

        var today = clock.GetBusinessToday();
        var generated = 0;
        var defaultCutOff = DateTime.DaysInMonth(today.Year, today.Month);

        // Cuentas: el corte "cae hoy" si PeriodEnd del mes == today.
        var accounts = await db.Accounts.AsNoTracking()
            .Select(a => new { a.IdAccount, a.IdUser })
            .ToListAsync(ct);
        foreach (var a in accounts)
        {
            foreach (var cutOff in DistinctCutOffs(db, a.IdAccount, defaultCutOff))
            {
                var (start, end) = StatementPeriod.Resolve(today.Year, today.Month, cutOff);
                if (end != today) continue;
                var exists = await db.Statements.AsNoTracking()
                    .AnyAsync(s => s.IdAccount == a.IdAccount && s.PeriodStart == start, ct);
                if (exists) continue;
                await statements.GenerateAsync(a.IdUser, a.IdAccount, today.Year, today.Month, cutOff, ct);
                generated++;
            }
        }

        // Tarjetas de crédito con corte hoy: statement base del periodo.
        var cardList = await db.CreditCards.AsNoTracking()
            .Where(c => c.Status == "active")
            .Select(c => new { c.IdCreditCard, c.IdUser, c.StatementCutOffDay })
            .ToListAsync(ct);
        foreach (var c in cardList)
        {
            var (_, end) = StatementPeriod.Resolve(today.Year, today.Month, c.StatementCutOffDay);
            if (end != today) continue;
            await cards.GenerateStatementAsync(c.IdUser, c.IdCreditCard, today.Year, today.Month, 0m, 0m, ct);
            generated++;
        }

        if (generated > 0) logger.LogInformation("Statements generados por trigger: {Count}", generated);
        return generated;
    }

    private static IEnumerable<int> DistinctCutOffs(AppDbContext db, int accountId, int defaultCutOff)
    {
        // Día de corte por defecto de la cuenta: se infiere del último statement;
        // sin historial, se usa fin de mes (corte calendario).
        var last = db.Statements.AsNoTracking()
            .Where(s => s.IdAccount == accountId)
            .OrderByDescending(s => s.PeriodEnd)
            .Select(s => (int?)s.CutOffDay)
            .FirstOrDefault();
        yield return last ?? defaultCutOff;
    }
}

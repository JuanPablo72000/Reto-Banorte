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
        t.Db.ChangeTracker.Clear();
        var users1 = t.Db.Users.AsNoTracking().Count();
        Assert.Equal(1, users1);
        DbSeeder.Seed(t.Db, t.Time); // segunda corrida no debe insertar
        t.Db.ChangeTracker.Clear();
        Assert.Equal(1, t.Db.Users.AsNoTracking().Count());
        Assert.All(t.Db.Users.AsNoTracking(), u => Assert.Equal(DateTimeKind.Utc, u.CreatedAt.Kind));
    }

    [Fact]
    public void Seeder_CreaGrafoDemo_Completo()
    {
        using var t = new TestDb();
        DbSeeder.Seed(t.Db, t.Time);
        // Lectura detached: lo trackeado en memoria no cuenta (mata #96).
        t.Db.ChangeTracker.Clear();
        Assert.NotEmpty(t.Db.Accounts.AsNoTracking().ToList());
        Assert.NotEmpty(t.Db.Transactions.AsNoTracking().ToList());
        Assert.NotEmpty(t.Db.Transfers.AsNoTracking().ToList());
        Assert.NotEmpty(t.Db.Sessions.AsNoTracking().ToList());
        Assert.NotEmpty(t.Db.AuditLogs.AsNoTracking().ToList());
        Assert.NotEmpty(t.Db.MemoryEvents.AsNoTracking().ToList());
        // Simulaciones: siempre hay transferencias pendientes confirmables.
        var pendientes = t.Db.Transfers.AsNoTracking().Where(x => x.Status == "pending").ToList();
        Assert.NotEmpty(pendientes);
        Assert.All(pendientes, p => Assert.Null(p.ConfirmedAt));
        Assert.Contains(t.Db.Transfers.AsNoTracking(), x => x.Status == "confirmed" && x.ConfirmedAt != null);
        Assert.Contains(t.Db.SavingsGoals.AsNoTracking(), g => g.Status == "active");
        Assert.Contains(t.Db.CreditCards.AsNoTracking(), c => c.Status == "active" && c.AvailableCredit > 0);
    }

    [Fact] // invariantes estables del seed rico (usuario demo, cuentas, ledger, memoria)
    public void Seeder_Snapshot_ValoresDemo()
    {
        using var t = new TestDb();
        DbSeeder.Seed(t.Db, t.Time);
        t.Db.ChangeTracker.Clear();

        var user = t.Db.Users.AsNoTracking().Single();
        Assert.Equal("Usuario Demo", user.Name);
        Assert.Equal("demo@banorte.mx", user.Email);
        Assert.Equal("es-MX", user.Locale);
        Assert.Equal("active", user.Status);

        var profile = t.Db.UserProfiles.AsNoTracking().Single();
        Assert.Equal(34, profile.Age);
        Assert.Equal("visual", profile.DisabilityType);

        var prefs = t.Db.AccessibilityPreferences.AsNoTracking().Single();
        Assert.Equal(1.25f, prefs.FontScale);
        Assert.True(prefs.HighContrast);
        Assert.False(prefs.DarkMode);
        Assert.True(prefs.ReducedMotion);
        Assert.True(prefs.LargeTargets);
        Assert.True(prefs.PlainLanguage);

        // Nómina es la primera cuenta (id_account 1 en BD fresca: el contexto
        // del frontend/MCP usa id_account=1).
        var accounts = t.Db.Accounts.AsNoTracking().OrderBy(a => a.IdAccount).ToList();
        Assert.Equal(4, accounts.Count);
        var nomina = accounts[0];
        Assert.Equal("debito", nomina.AccountType);
        Assert.Equal("Nómina", nomina.Alias);
        Assert.Equal("****1234", nomina.MaskedNumber);
        Assert.Equal("MXN", nomina.Currency);
        Assert.Equal("active", nomina.Status);
        Assert.Contains(accounts, a => a.Status == "blocked");

        // Ledger rico: cientos de movimientos con variedad de estados,
        // direcciones y categorías; saldos coherentes con el cierre diario.
        var txs = t.Db.Transactions.AsNoTracking().ToList();
        Assert.True(txs.Count > 100, $"esperados >100 movimientos, obtuvo {txs.Count}");
        Assert.Contains(txs, x => x.Direction == "credit" && x.Category == "nomina" && x.Description == "Pago nómina quincenal");
        Assert.Contains(txs, x => x.Status == "pending");
        Assert.Contains(txs, x => x.Status == "failed");
        Assert.Contains(txs, x => x.Direction == "debit" && x.Category == "pago_tarjeta");
        Assert.Contains(txs, x => x.IdExpenseCategory != null);

        foreach (var acc in accounts.Where(a => a.Status == "active" && a.Alias != "Cuenta antigua"))
        {
            var ultimo = t.Db.DailyBalances.AsNoTracking()
                .Where(d => d.IdAccount == acc.IdAccount)
                .OrderByDescending(d => d.Date)
                .FirstOrDefault();
            Assert.NotNull(ultimo);
            Assert.Equal(ultimo!.ClosingBalance, acc.Balance); // saldo == cierre del ledger
        }

        // Transferencias: la clásica pendiente "Mamá" sigue existiendo y es confirmable.
        var transfer = t.Db.Transfers.AsNoTracking()
            .Single(x => x.Status == "pending" && x.DestinationAlias == "Mamá" && x.Concept == "Apoyo");
        Assert.Equal("****5678", transfer.DestinationMasked);
        Assert.Equal("MXN", transfer.Currency);
        Assert.Null(transfer.ConfirmedAt);
        Assert.Contains(t.Db.Transfers.AsNoTracking(), x => x.Status == "rejected");

        var confirmation = t.Db.TransferConfirmations.AsNoTracking()
            .Single(c => c.IdTransfer == transfer.IdTransfer);
        Assert.Equal("app", confirmation.Method);
        Assert.Equal("pending", confirmation.Status);

        // Conciliación: matched + pending + unmatched.
        var matches = t.Db.ReconciliationMatches.AsNoTracking().ToList();
        Assert.Contains(matches, m => m.Status == "matched");
        Assert.Contains(matches, m => m.Status == "pending");
        Assert.Contains(matches, m => m.Status == "unmatched");

        // Finanzas personales variadas.
        Assert.Equal(3, t.Db.CreditCards.AsNoTracking().Count());
        Assert.Equal(5, t.Db.SavingsGoals.AsNoTracking().Count());
        Assert.Equal(4, t.Db.SavingsGoals.AsNoTracking().Count(g => g.Status == "active"));
        var hoy = DateOnly.FromDateTime(TestDb.FixedNow.UtcDateTime.Date);
        Assert.Contains(t.Db.Budgets.AsNoTracking(), b => b.Month == hoy.Month && b.Year == hoy.Year);
        Assert.Contains(t.Db.Budgets.AsNoTracking(), b => b.Status == "exceeded");
        Assert.Contains(t.Db.Statements.AsNoTracking(), s => s.AccountType == "debito" && s.Status == "generated");
        Assert.Contains(t.Db.Statements.AsNoTracking(), s => s.AccountType == "credito" && s.Status == "generated");
        Assert.NotEmpty(t.Db.StatementExpenses.AsNoTracking().ToList());

        // Memoria variada.
        Assert.Equal(3, t.Db.Sessions.AsNoTracking().Count());
        Assert.Contains(t.Db.Sessions.AsNoTracking(), s => s.DeviceContext == "web");
        Assert.Contains(t.Db.Sessions.AsNoTracking(), s => s.DeviceContext == "android");

        Assert.Contains(t.Db.DetectedPreferences.AsNoTracking(),
            d => d.PreferenceType == "fontScale" && d.Value == "1.25");
        Assert.True(t.Db.DetectedPreferences.AsNoTracking().Count() >= 3);

        var memories = t.Db.MemoryEvents.AsNoTracking().ToList();
        Assert.True(memories.Count >= 5);
        Assert.Contains(memories, m => m.EventType == "zoom" && m.Intent == "aumentar-legibilidad"
            && m.TargetElement == "balance-card" && m.RedactedSummary == "usuario amplía texto"
            && m.SensitivityLevel == "low");
        Assert.Contains(memories, m => m.EventType == "contrast");
        Assert.Contains(memories, m => m.EventType == "motion");

        var audit = t.Db.AuditLogs.AsNoTracking().Single(a => a.Action == "seed");
        Assert.Equal("database", audit.Resource);
        Assert.Equal("ok", audit.Result);
        Assert.Equal("low", audit.RiskLevel);
        Assert.Equal("seed inicial", audit.RedactedPayload);
        Assert.Contains(t.Db.AuditLogs.AsNoTracking(), a => a.Action == "transfer.confirm");

        // UTC en todo el grafo.
        Assert.All(t.Db.Users.AsNoTracking(), u => Assert.Equal(DateTimeKind.Utc, u.CreatedAt.Kind));
        Assert.All(t.Db.Transfers.AsNoTracking(), x => Assert.Equal(DateTimeKind.Utc, x.CreatedAt.Kind));
    }

    [Fact] // mata #24: índice único de email
    public async Task EmailDuplicado_ViolaIndiceUnico()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        t.Db.Users.Add(new User { Name = "A", Email = "dup@x.mx", PasswordHash = "x", CreatedAt = now });
        await t.Db.SaveChangesAsync();
        t.Db.Users.Add(new User { Name = "B", Email = "dup@x.mx", PasswordHash = "x", CreatedAt = now });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }

    [Fact] // mata #25/#26: relación y unicidad User-UserProfile
    public async Task SegundoUserProfile_ViolaIndiceUnico()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "A", Email = "pf@x.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        t.Db.UserProfiles.Add(new UserProfile { IdUser = u.IdUser, Age = 30, DisabilityType = "x", UpdatedAt = now });
        await t.Db.SaveChangesAsync();
        // Detach: si el primer perfil sigue trackeado, el fixup uno-a-uno lo marca
        // Deleted al agregar el segundo y el INSERT nunca viola el índice.
        t.Db.ChangeTracker.Clear();
        t.Db.UserProfiles.Add(new UserProfile { IdUser = u.IdUser, Age = 31, DisabilityType = "y", UpdatedAt = now });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }

    [Fact] // mata #28 (índice) y relación #64-68: segunda preferencia del mismo usuario
    public async Task SegundaAccessibilityPreference_ViolaIndiceUnico()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "A", Email = "ap@x.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        t.Db.AccessibilityPreferences.Add(new AccessibilityPreference { IdUser = u.IdUser, UpdatedAt = now });
        await t.Db.SaveChangesAsync();
        t.Db.ChangeTracker.Clear(); // ver comentario en SegundoUserProfile
        t.Db.AccessibilityPreferences.Add(new AccessibilityPreference { IdUser = u.IdUser, UpdatedAt = now });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }

    [Fact] // mata #25 (relación uno-a-uno): sin cascade el perfil huérfano sobrevive
    public async Task BorrarUsuario_EliminaPerfilEnCascada()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "A", Email = "cs@x.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        t.Db.UserProfiles.Add(new UserProfile { IdUser = u.IdUser, Age = 30, DisabilityType = "x", UpdatedAt = now });
        t.Db.AccessibilityPreferences.Add(new AccessibilityPreference { IdUser = u.IdUser, UpdatedAt = now });
        await t.Db.SaveChangesAsync();

        t.Db.Users.Remove(u);
        await t.Db.SaveChangesAsync();

        t.Db.ChangeTracker.Clear();
        Assert.Empty(t.Db.UserProfiles.AsNoTracking().ToList());
        Assert.Empty(t.Db.AccessibilityPreferences.AsNoTracking().ToList());
    }

    [Fact] // mata #44 y #46: unicidad de ReconciliationMatch por transfer y por transaction
    public async Task ReconciliationMatch_Duplicado_ViolaIndicesUnicos()
    {
        using var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "A", Email = "rc@x.mx", PasswordHash = "x", CreatedAt = now };
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
        var tx1 = new Transaction { IdAccount = acc.IdAccount, Date = day, Amount = 1m, Direction = "debit", Category = "c", Description = "d1", Status = "posted", Reference = "R1" };
        var tx2 = new Transaction { IdAccount = acc.IdAccount, Date = day, Amount = 2m, Direction = "debit", Category = "c", Description = "d2", Status = "posted", Reference = "R2" };
        t.Db.Transactions.AddRange(tx1, tx2);
        await t.Db.SaveChangesAsync();
        var tr1 = new Transfer { IdUser = u.IdUser, IdOriginAccount = acc.IdAccount, DestinationAlias = "A", DestinationMasked = "****1", Amount = 1m, Status = "confirmed", IdempotencyKey = "rc-1", ConfirmedAt = now };
        var tr2 = new Transfer { IdUser = u.IdUser, IdOriginAccount = acc.IdAccount, DestinationAlias = "B", DestinationMasked = "****2", Amount = 2m, Status = "confirmed", IdempotencyKey = "rc-2", ConfirmedAt = now };
        t.Db.Transfers.AddRange(tr1, tr2);
        await t.Db.SaveChangesAsync();

        t.Db.ReconciliationMatches.Add(new ReconciliationMatch
            { IdTransfer = tr1.IdTransfer, IdTransaction = tx1.IdTransaction, Status = "matched", MatchScore = 1f, MatchedAt = now, Notes = "" });
        await t.Db.SaveChangesAsync();
        // Detach: el fixup uno-a-uno requerido huérfana-elimina el match previo
        // al agregar otro con el mismo transfer/transaction (ver SegundoUserProfile).
        t.Db.ChangeTracker.Clear();

        // Mismo transfer, otra transacción -> viola IX por transfer.
        t.Db.ReconciliationMatches.Add(new ReconciliationMatch
            { IdTransfer = tr1.IdTransfer, IdTransaction = tx2.IdTransaction, Status = "matched", MatchScore = 1f, MatchedAt = now, Notes = "" });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
        t.Db.ChangeTracker.Clear();

        // Misma transacción, otro transfer -> viola IX por transaction.
        t.Db.ReconciliationMatches.Add(new ReconciliationMatch
            { IdTransfer = tr2.IdTransfer, IdTransaction = tx1.IdTransaction, Status = "matched", MatchScore = 1f, MatchedAt = now, Notes = "" });
        await Assert.ThrowsAsync<DbUpdateException>(() => t.Db.SaveChangesAsync());
    }
}

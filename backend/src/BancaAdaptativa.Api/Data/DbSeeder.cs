using BancaAdaptativa.Api.Models;

namespace BancaAdaptativa.Api.Data;

public static class DbSeeder
{
    public static void Seed(AppDbContext db, TimeProvider timeProvider)
    {
        if (db.Users.Any()) return;

        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var today = DateOnly.FromDateTime(nowUtc.Date);

        var user = new User
        {
            Name = "Usuario Demo",
            Email = "demo@banorte.mx",
            PasswordHash = BCrypt.Net.BCrypt.HashPassword("Demo123!"),
            Locale = "es-MX",
            Status = "active",
            CreatedAt = nowUtc
        };
        db.Users.Add(user);
        db.SaveChanges();

        db.UserProfiles.Add(new UserProfile { IdUser = user.IdUser, Age = 34, DisabilityType = "visual", UpdatedAt = nowUtc });
        db.AccessibilityPreferences.Add(new AccessibilityPreference
        {
            IdUser = user.IdUser, FontScale = 1.25f, HighContrast = true,
            DarkMode = false, ReducedMotion = true, LargeTargets = true,
            PlainLanguage = true, UpdatedAt = nowUtc
        });

        var account = new Account
        {
            IdUser = user.IdUser, AccountType = "debito", Alias = "Nómina",
            MaskedNumber = "****1234", Currency = "MXN", Balance = 25400.50m,
            Status = "active", CreatedAt = nowUtc
        };
        db.Accounts.Add(account);
        db.SaveChanges();

        db.Transactions.AddRange(
            new Transaction { IdAccount = account.IdAccount, Date = today.AddDays(-2), Amount = 15000m, Direction = "credit", Category = "nomina", Description = "Pago nómina", Status = "posted", Reference = "NOM-001" },
            new Transaction { IdAccount = account.IdAccount, Date = today.AddDays(-1), Amount = 850.75m, Direction = "debit", Category = "super", Description = "Súper", Status = "posted", Reference = "SUP-002" },
            new Transaction { IdAccount = account.IdAccount, Date = today, Amount = 320m, Direction = "debit", Category = "transporte", Description = "Transporte", Status = "posted", Reference = "TRN-003" });
        db.SaveChanges();

        db.DailyBalances.Add(new DailyBalance
        {
            IdAccount = account.IdAccount, Date = today,
            OpeningBalance = 26000m, Income = 0m, Expenses = 1170.75m, ClosingBalance = 24829.25m
        });

        var transfer = new Transfer
        {
            IdUser = user.IdUser, IdOriginAccount = account.IdAccount,
            DestinationAlias = "Mamá", DestinationMasked = "****5678",
            Amount = 2000m, Currency = "MXN", Concept = "Apoyo",
            Status = "pending", IdempotencyKey = Guid.NewGuid().ToString(), ConfirmedAt = null
        };
        db.Transfers.Add(transfer);
        db.SaveChanges();

        db.TransferConfirmations.Add(new TransferConfirmation
        {
            IdTransfer = transfer.IdTransfer, Method = "app", Status = "pending", ConfirmedAt = null
        });

        var session = new Session { IdUser = user.IdUser, StartedAt = nowUtc, EndedAt = null, DeviceContext = "web" };
        db.Sessions.Add(session);
        db.SaveChanges();

        var detected = new DetectedPreference
        {
            IdUser = user.IdUser, PreferenceType = "fontScale", Value = "1.25",
            ConfidenceScore = 0.87f, BasedOnEventsCount = 5, UpdatedAt = nowUtc
        };
        db.DetectedPreferences.Add(detected);
        db.SaveChanges();

        db.MemoryEvents.Add(new MemoryEvent
        {
            IdSession = session.IdSession, IdUser = user.IdUser, IdDetectedPreference = detected.IdDetected,
            EventType = "zoom", Intent = "aumentar-legibilidad", TargetElement = "balance-card",
            RedactedSummary = "usuario amplía texto", SensitivityLevel = "low",
            CreatedAt = nowUtc, RetentionUntil = nowUtc.AddDays(90)
        });

        db.AuditLogs.Add(new AuditLog
        {
            IdUser = user.IdUser, Action = "seed", Resource = "database",
            Result = "ok", RiskLevel = "low", RedactedPayload = "seed inicial",
            CreatedAt = nowUtc
        });

        db.SaveChanges();
    }
}

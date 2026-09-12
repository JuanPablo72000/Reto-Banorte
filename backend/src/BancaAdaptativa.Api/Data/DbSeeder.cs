using BancaAdaptativa.Api.Models;

namespace BancaAdaptativa.Api.Data;

public static class DbSeeder
{
    public static void Seed(AppDbContext db, TimeProvider timeProvider)
    {
        EnsureExpenseCategories(db);

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

        var supermarket = db.ExpenseCategories.Single(c => c.Code == "supermarket");
        var transport = db.ExpenseCategories.Single(c => c.Code == "transport");

        db.Transactions.AddRange(
            new Transaction { IdAccount = account.IdAccount, Date = today.AddDays(-2), Amount = 15000m, Direction = "credit", Category = "nomina", Description = "Pago nómina", Status = "posted", Reference = "NOM-001" },
            new Transaction { IdAccount = account.IdAccount, Date = today.AddDays(-1), Amount = 850.75m, Direction = "debit", Category = "super", Description = "Súper", Status = "posted", Reference = "SUP-002", IdExpenseCategory = supermarket.IdCategory },
            new Transaction { IdAccount = account.IdAccount, Date = today, Amount = 320m, Direction = "debit", Category = "transporte", Description = "Transporte", Status = "posted", Reference = "TRN-003", IdExpenseCategory = transport.IdCategory });
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
            Status = "pending", IdempotencyKey = Guid.NewGuid().ToString(),
            CreatedAt = nowUtc, ConfirmedAt = null
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

        SeedPersonalFinanceDemo(db, user.IdUser, account.IdAccount, today, nowUtc);
    }

    private static void EnsureExpenseCategories(AppDbContext db)
    {
        if (db.ExpenseCategories.Any()) return;
        db.ExpenseCategories.AddRange(
            new ExpenseCategory { Name = "Gasolina", Code = "gas", Icon = "fuel", IsDefault = true, SortOrder = 1 },
            new ExpenseCategory { Name = "Restaurantes", Code = "restaurant", Icon = "restaurant", IsDefault = true, SortOrder = 2 },
            new ExpenseCategory { Name = "Comida rápida", Code = "fast_food", Icon = "fastfood", IsDefault = true, SortOrder = 3 },
            new ExpenseCategory { Name = "Farmacia", Code = "drugstore", Icon = "pharmacy", IsDefault = true, SortOrder = 4 },
            new ExpenseCategory { Name = "Servicios médicos", Code = "medical", Icon = "medical", IsDefault = true, SortOrder = 5 },
            new ExpenseCategory { Name = "Supermercados", Code = "supermarket", Icon = "cart", IsDefault = true, SortOrder = 6 },
            new ExpenseCategory { Name = "Transporte", Code = "transport", Icon = "transport", IsDefault = true, SortOrder = 7 },
            new ExpenseCategory { Name = "Entretenimiento", Code = "entertainment", Icon = "entertainment", IsDefault = true, SortOrder = 8 },
            new ExpenseCategory { Name = "Educación", Code = "education", Icon = "education", IsDefault = true, SortOrder = 9 },
            new ExpenseCategory { Name = "Servicios básicos", Code = "utilities", Icon = "utilities", IsDefault = true, SortOrder = 10 });
        db.SaveChanges();
    }

    private static void SeedPersonalFinanceDemo(AppDbContext db, int idUser, int idAccount, DateOnly today, DateTime nowUtc)
    {
        var supermarket = db.ExpenseCategories.Single(c => c.Code == "supermarket");
        var monthStart = new DateTime(today.Year, today.Month, 1, 0, 0, 0, DateTimeKind.Utc);

        // Presupuesto demo del mes en curso.
        db.Budgets.Add(new Budget
        {
            IdUser = idUser, IdExpenseCategory = supermarket.IdCategory,
            Month = today.Month, Year = today.Year,
            AmountLimit = 5000m, CurrentSpent = 850.75m,
            StartDate = monthStart, EndDate = monthStart.AddMonths(1).AddTicks(-1),
            Status = "active", CreatedAt = nowUtc, UpdatedAt = nowUtc
        });

        // Meta de ahorro demo.
        db.SavingsGoals.Add(new SavingsGoal
        {
            IdUser = idUser, Name = "Fondo de emergencia",
            TargetAmount = 50000m, CurrentAmount = 12500m,
            TargetDate = nowUtc.AddMonths(6),
            Status = "active", CreatedAt = nowUtc, UpdatedAt = nowUtc
        });

        // Estado de cuenta demo del periodo que cierra hoy (incluye las 3 txs seed).
        var cutOff = today.Day;
        var prev = today.AddMonths(-1);
        var prevEnd = new DateOnly(prev.Year, prev.Month, Math.Min(cutOff, DateTime.DaysInMonth(prev.Year, prev.Month)));
        var start = prevEnd.AddDays(1);
        var stmt = new Statement
        {
            IdAccount = idAccount, CutOffDay = cutOff,
            PeriodStart = start, PeriodEnd = today,
            OpeningBalance = 0m, ClosingBalance = 13829.25m,
            TotalCredits = 15000m, TotalDebits = 1170.75m, TransactionCount = 3,
            AccountType = "debito", Status = "generated", GeneratedAt = nowUtc
        };
        db.Statements.Add(stmt);
        db.SaveChanges();
        db.StatementExpenses.AddRange(
            new StatementExpense
            {
                IdStatement = stmt.IdStatement, IdExpenseCategory = supermarket.IdCategory,
                Amount = 850.75m, TransactionCount = 1,
                FirstTransactionDate = today.AddDays(-1), LastTransactionDate = today.AddDays(-1)
            },
            new StatementExpense
            {
                IdStatement = stmt.IdStatement,
                IdExpenseCategory = db.ExpenseCategories.Single(c => c.Code == "transport").IdCategory,
                Amount = 320m, TransactionCount = 1,
                FirstTransactionDate = today, LastTransactionDate = today
            });
        db.SaveChanges();

        // Tarjeta de crédito demo + su statement base.
        var card = new CreditCard
        {
            IdUser = idUser, CardNumberMasked = "****5678", CardType = "Visa",
            CreditLimit = 30000m, AvailableCredit = 27749.50m, InterestRate = 24m,
            StatementCutOffDay = 15, PaymentDueDay = 5,
            Status = "active", CreatedAt = nowUtc
        };
        db.CreditCards.Add(card);
        db.SaveChanges();

        var cardEndDay = Math.Min(15, DateTime.DaysInMonth(today.Year, today.Month));
        var cardEnd = new DateOnly(today.Year, today.Month, cardEndDay);
        var cardPrev = cardEnd.AddMonths(-1);
        var cardPrevEnd = new DateOnly(cardPrev.Year, cardPrev.Month, Math.Min(15, DateTime.DaysInMonth(cardPrev.Year, cardPrev.Month)));
        var cardStmtBase = new Statement
        {
            IdAccount = idAccount, CutOffDay = 15,
            PeriodStart = cardPrevEnd.AddDays(1), PeriodEnd = cardEnd,
            OpeningBalance = 0m, ClosingBalance = 2250.50m,
            TotalCredits = 1000m, TotalDebits = 3250.50m, TransactionCount = 0,
            AccountType = "credito", Status = "generated", GeneratedAt = nowUtc
        };
        db.Statements.Add(cardStmtBase);
        db.SaveChanges();
        var dueDay = Math.Min(5, DateTime.DaysInMonth(cardEnd.Year, cardEnd.Month));
        db.CreditCardStatements.Add(new CreditCardStatement
        {
            IdCreditCard = card.IdCreditCard, IdStatement = cardStmtBase.IdStatement,
            PreviousBalance = 0m, TotalPayments = 1000m, TotalCredits = 1000m,
            TotalPurchases = 3250.50m, InterestCharges = 0m, MinimumPayment = 112.53m,
            PaymentDueDate = new DateOnly(cardEnd.Year, cardEnd.Month, dueDay),
            AvailableCredit = 27749.50m, Status = "generated", GeneratedAt = nowUtc
        });
        db.SaveChanges();
    }
}

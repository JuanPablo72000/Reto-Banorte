using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;

namespace BancaAdaptativa.Api.Data;

/// <summary>
/// Seed demo rico y determinista: 90 días de movimientos en varias cuentas,
/// balances diarios coherentes, transferencias en todos sus estados (con
/// conciliación), presupuestos del mes calculados del gasto real, metas de
/// ahorro, estados de cuenta de meses cerrados y 3 tarjetas de crédito.
/// Todo se genera con un Random con semilla fija relativo a "today" del
/// TimeProvider, así que cada corrida fresca produce la misma historia.
///
/// Invariantes que sostienen las simulaciones sin error:
///  - La cuenta Nómina se crea primera (id_account 1 en BD fresca).
///  - Balance de cada cuenta == cierre de su último DailyBalance == suma del ledger.
///  - Hay transferencias "pending" confirmables (ConfirmAsync exige pending).
///  - Hay metas "active" (ContributeAsync exige active) y tarjetas con crédito pagable.
///  - Índices únicos respetados: DailyBalance(cuenta,fecha), Statement(cuenta,PeriodStart),
///    StatementExpense(statement,categoría), Budget(user,categoría,mes,año),
///    Transfer.IdempotencyKey, ReconciliationMatch 1:1 por transfer y por transaction.
/// </summary>
public static class DbSeeder
{
    private const int RandomSeed = 20260901;
    private const int DiasHistorial = 90;
    private const decimal SaldoInicialNomina = 65000m;
    private const decimal SaldoInicialAhorro = 95000m;
    private const decimal SaldoInicialCompras = 9000m;

    // Espec de tarjeta: también la usa el ledger para los pagos mensuales.
    private sealed record CardSpec(
        string Masked, string Tipo, decimal Limite, double Tasa, int Corte, int Pago,
        decimal ComprasMes, decimal PagoMensual);

    private static readonly CardSpec[] Tarjetas =
    [
        new("****4021", "Visa Oro", 50000m, 3.2, 15, 5, 12850.40m, 1300m),
        new("****7734", "Mastercard Estándar", 30000m, 3.8, 22, 12, 8420.75m, 2000m),
        new("****1002", "Visa Platino Vive+", 120000m, 2.4, 28, 8, 21400.00m, 6500m),
    ];

    // Transferencias externas confirmadas: su transacción debit vive en el
    // ledger (referencia exacta), así monto/fecha/conciliación cuadran.
    private static readonly (string Ref, string Alias, string Masked, string Concepto, string Metodo)[] TransferExternas =
    [
        ("TEXT1", "Mamá", "****5678", "Apoyo mensual", "app"),
        ("TEXT2", "Papá", "****2210", "Apoyo mensual", "token"),
        ("TEXT3", "Juan Pablo (amigo)", "****8891", "Dividir cena", "app"),
        ("TEXT4", "Colegiatura ITM", "****3041", "Pago colegiatura", "token"),
        ("TEXT5", "Carlos (préstamo)", "****6620", "Préstamo personal", "app"),
    ];

    // Movimiento del ledger antes de materializarlo como Transaction.
    private sealed record Mov(
        string Cuenta, DateOnly Fecha, decimal Monto, string Direction,
        string Category, string Description, string Status, string Reference,
        string? ExpCode);

    public static void Seed(AppDbContext db, TimeProvider timeProvider)
    {
        EnsureExpenseCategories(db);

        if (db.Users.Any()) return;

        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var today = DateOnly.FromDateTime(nowUtc.Date);
        var rng = new Random(RandomSeed);

        // ---------------- Usuario demo (identidad estable: tests + login) ----
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
        db.SaveChanges();

        // ---------------- Cuentas (Nómina primero: id_account 1) ------------
        var nomina = NewAccount(user.IdUser, "debito", "Nómina", "****1234", nowUtc);
        var ahorro = NewAccount(user.IdUser, "ahorro", "Ahorro", "****4321", nowUtc);
        var compras = NewAccount(user.IdUser, "debito", "Compras en línea", "****7788", nowUtc);
        var antigua = NewAccount(user.IdUser, "debito", "Cuenta antigua", "****0002", nowUtc, status: "blocked");
        db.Accounts.AddRange(nomina, ahorro, compras, antigua);
        db.SaveChanges();

        var cuentas = new Dictionary<string, Account>
        {
            ["nomina"] = nomina, ["ahorro"] = ahorro, ["compras"] = compras,
        };

        // ---------------- Ledger de 90 días --------------------------------
        var categorias = db.ExpenseCategories.ToDictionary(c => c.Code, c => c.IdCategory);
        var ledger = BuildLedger(today, rng);

        var seq = 0;
        var transacciones = new List<Transaction>();
        foreach (var m in ledger)
        {
            seq++;
            transacciones.Add(new Transaction
            {
                IdAccount = cuentas[m.Cuenta].IdAccount,
                Date = m.Fecha,
                Amount = Math.Round(m.Monto, 2),
                Direction = m.Direction,
                Category = m.Category,
                Description = m.Description,
                Status = m.Status,
                Reference = m.Reference.Length == 0 ? $"SD-{seq:D4}" : m.Reference,
                IdExpenseCategory = m.ExpCode is not null && categorias.TryGetValue(m.ExpCode, out var idCat) ? idCat : null
            });
        }
        db.Transactions.AddRange(transacciones);
        db.SaveChanges();

        // ---------------- Balances diarios + saldo final coherente ----------
        foreach (var (alias, account) in cuentas)
        {
            var dias = alias == "compras" ? 30 : DiasHistorial;
            var porDia = transacciones
                .Where(t => t.IdAccount == account.IdAccount && t.Status == "posted")
                .GroupBy(t => t.Date)
                .ToDictionary(g => g.Key, g => (
                    income: g.Where(t => t.Direction == "credit").Sum(t => t.Amount),
                    expenses: g.Where(t => t.Direction == "debit").Sum(t => t.Amount)));

            var inicio = today.AddDays(-(dias - 1));
            var cierreAnterior = 0m;
            var balances = new List<DailyBalance>();
            for (var d = inicio; d <= today; d = d.AddDays(1))
            {
                var (income, expenses) = porDia.TryGetValue(d, out var v) ? v : (income: 0m, expenses: 0m);
                var cierre = cierreAnterior + income - expenses;
                balances.Add(new DailyBalance
                {
                    IdAccount = account.IdAccount, Date = d,
                    OpeningBalance = cierreAnterior, Income = income,
                    Expenses = expenses, ClosingBalance = cierre
                });
                cierreAnterior = cierre;
            }
            db.DailyBalances.AddRange(balances);
            account.Balance = Math.Round(cierreAnterior, 2);
        }
        db.SaveChanges();

        // ---------------- Transferencias + conciliación ---------------------
        SeedTransfers(db, user.IdUser, nomina, transacciones, today, nowUtc);

        // ---------------- Presupuestos del mes en curso ---------------------
        SeedBudgets(db, user.IdUser, transacciones, categorias, today, nowUtc, rng);

        // ---------------- Metas de ahorro ----------------------------------
        db.SavingsGoals.AddRange(
            NewGoal(user.IdUser, "Fondo de emergencia", 50000m, 18750m, nowUtc.AddMonths(6), "active", nowUtc),
            NewGoal(user.IdUser, "Viaje a Japón", 80000m, 41200m, nowUtc.AddMonths(10), "active", nowUtc),
            NewGoal(user.IdUser, "Enganche del auto", 350000m, 152400m, nowUtc.AddMonths(18), "active", nowUtc),
            NewGoal(user.IdUser, "Laptop nueva", 28000m, 24600m, nowUtc.AddMonths(2), "active", nowUtc),
            NewGoal(user.IdUser, "Bici eléctrica", 15000m, 15000m, nowUtc.AddMonths(-1), "completed", nowUtc));
        db.SaveChanges();

        // ---------------- Estados de cuenta (meses cerrados) ----------------
        SeedStatements(db, nomina, transacciones, nowUtc, today);

        // ---------------- Tarjetas de crédito (3, con statement previo) -----
        SeedCreditCards(db, user.IdUser, nomina, today, nowUtc);

        // ---------------- Sesiones / memoria / auditoría --------------------
        SeedMemoryAndAudit(db, user.IdUser, nowUtc);
    }

    private static Account NewAccount(int idUser, string type, string alias, string masked, DateTime nowUtc, string status = "active") =>
        new()
        {
            IdUser = idUser, AccountType = type, Alias = alias,
            MaskedNumber = masked, Currency = "MXN", Balance = 0m,
            Status = status, CreatedAt = nowUtc.AddDays(-DiasHistorial)
        };

    private static SavingsGoal NewGoal(int idUser, string name, decimal target, decimal current, DateTime targetDate, string status, DateTime nowUtc) =>
        new()
        {
            IdUser = idUser, Name = name, TargetAmount = target, CurrentAmount = current,
            TargetDate = targetDate, Status = status, CreatedAt = nowUtc.AddMonths(-8), UpdatedAt = nowUtc
        };

    // ---------------------------------------------------------------------
    // Ledger: saldos iniciales + ingresos recurrentes + pagos fijos + pagos
    // de tarjetas + traspasos + transferencias externas + gasto diario.
    // ---------------------------------------------------------------------
    private static List<Mov> BuildLedger(DateOnly today, Random rng)
    {
        var movs = new List<Mov>();
        var inicio = today.AddDays(-(DiasHistorial - 1));
        var refSeq = 0;
        string Ref(string prefijo) => $"{prefijo}-{++refSeq:D4}";

        // Saldos iniciales.
        movs.Add(new Mov("nomina", inicio, SaldoInicialNomina, "credit", "traspaso", "Saldo inicial traspasado", "posted", "INI-0001", null));
        movs.Add(new Mov("ahorro", inicio, SaldoInicialAhorro, "credit", "traspaso", "Saldo inicial traspasado", "posted", "INI-0002", null));
        movs.Add(new Mov("compras", today.AddDays(-29), SaldoInicialCompras, "credit", "traspaso", "Saldo inicial traspasado", "posted", "INI-0003", null));

        // Transferencias externas confirmadas (debit en Nómina; SeedTransfers
        // las liga por referencia exacta).
        movs.Add(new Mov("nomina", today.AddDays(-20), 2000m, "debit", "transferencia", "Transferencia a Mamá — apoyo", "posted", "TEXT1", null));
        movs.Add(new Mov("nomina", today.AddDays(-35), 3500m, "debit", "transferencia", "Transferencia a Papá — apoyo mensual", "posted", "TEXT2", null));
        movs.Add(new Mov("nomina", today.AddDays(-8), 480m, "debit", "transferencia", "Traspaso cena — Juan Pablo", "posted", "TEXT3", null));
        movs.Add(new Mov("nomina", today.AddDays(-12), 5600m, "debit", "educacion", "Pago colegiatura ITM", "posted", "TEXT4", "education"));
        movs.Add(new Mov("nomina", today.AddDays(-55), 1800m, "debit", "transferencia", "Préstamo a Carlos", "posted", "TEXT5", null));

        var supermercados = new[] { "Walmart Express", "Chedraui Selecto", "Soriana Híper", "Costco Polanco", "La Comer" };
        var comidaRapida = new[] { "McDonald's", "Tacos El Güero", "Domino's Pizza", "Starbucks Reforma", "KFC" };
        var restaurantes = new[] { "La Destilería", "Vips Universidad", "Sushi Roll", "P.F. Chang's", "El Cardenal" };
        var transporte = new[] { "Uber", "DiDi", "Metro CDMX", "Ecobici", "Peaje VIA Pass" };
        var gasolina = new[] { "Gasolina Pemex", "Shell Plus", "Mobil" };
        var farmacia = new[] { "Farmacia Guadalajara", "Farmacias del Ahorro", "Benavides" };
        var entretenimiento = new[] { "Cinépolis", "Steam", "Boleto concierto", "Six Flags" };
        var educacion = new[] { "Udemy", "Librería Gandhi", "Coursera", "Domestika" };
        var medico = new[] { "Consulta Dra. Fuentes", "Laboratorio Santa Fe", "Clínica dental Sonrisa", "Farmacia con consultorio" };

        decimal Monto(double min, double max) => Math.Round((decimal)(min + rng.NextDouble() * (max - min)), 2);
        decimal MontoPar(double min, double max) => Math.Round(Monto(min, max) / 5m) * 5m;

        for (var d = inicio; d <= today; d = d.AddDays(1))
        {
            var dia = d.Day;
            var ultimoDia = dia == DateTime.DaysInMonth(d.Year, d.Month);
            var esFinDeSemana = d.DayOfWeek is DayOfWeek.Saturday or DayOfWeek.Sunday;

            // --- Ingresos ---
            if (dia == 15 || ultimoDia)
                movs.Add(new Mov("nomina", d, 24500m, "credit", "nomina", "Pago nómina quincenal", "posted", Ref("NOM"), null));
            if (dia == 7)
                movs.Add(new Mov("nomina", d, MontoPar(2500, 7000), "credit", "freelance", "Proyecto freelance — diseño de interfaz", "posted", Ref("FRE"), null));
            if (dia == 22 && rng.NextDouble() < 0.6)
                movs.Add(new Mov("nomina", d, MontoPar(800, 2500), "credit", "freelance", "Asesoría consultoría TI", "posted", Ref("FRE"), null));
            if (dia == 1 && d > inicio)
                movs.Add(new Mov("ahorro", d, Monto(380, 620), "credit", "intereses", "Intereses mensuales cuenta ahorro", "posted", Ref("INT"), null));
            if (dia == 18 && rng.NextDouble() < 0.5)
                movs.Add(new Mov("compras", d, Monto(50, 250), "credit", "cashback", "Cashback programa de recompensas", "posted", Ref("CSH"), null));

            // --- Pagos fijos ---
            if (dia == 1 && d > inicio)
            {
                movs.Add(new Mov("nomina", d, 8500m, "debit", "renta", "Renta departamento", "posted", Ref("REN"), null));
                movs.Add(new Mov("nomina", d, 320m, "debit", "servicios", "Agua CDMX bimestral", "posted", Ref("AGU"), "utilities"));
            }
            if (dia == 5)
                movs.Add(new Mov("nomina", d, 229m, "debit", "suscripcion", "Netflix premium", "posted", Ref("NFLX"), "entertainment"));
            if (dia == 8)
                movs.Add(new Mov("nomina", d, 129m, "debit", "suscripcion", "Spotify familiar", "posted", Ref("SPTF"), "entertainment"));
            if (dia == 12)
                movs.Add(new Mov("nomina", d, 49m, "debit", "suscripcion", "iCloud 200GB", "posted", Ref("ICLD"), null));
            if (dia == 17)
                movs.Add(new Mov("nomina", d, 549m, "debit", "servicios", "Telmex Infinitum", "posted", Ref("TLMX"), "utilities"));
            if (dia == 10 && d.Month % 2 == 0)
                movs.Add(new Mov("nomina", d, Monto(380, 920), "debit", "servicios", "CFE bimestral", "posted", Ref("CFE"), "utilities"));
            if (d.DayOfWeek == DayOfWeek.Monday)
                movs.Add(new Mov("nomina", d, 137.5m, "debit", "gym", "Gimnasio Smart Fit semanal", "posted", Ref("GYM"), null));

            // --- Pagos de tarjetas de crédito (coinciden con SeedCreditCards) ---
            foreach (var c in Tarjetas)
            {
                if (dia == c.Corte + 1)
                    movs.Add(new Mov("nomina", d, c.PagoMensual, "debit", "pago_tarjeta",
                        $"Pago tarjeta {c.Tipo} {c.Masked}", "posted", $"PTC-{c.Corte:D2}-{d.Month:D2}", null));
            }

            // --- Traspaso mensual Nómina -> Ahorro (meta mensual) ---
            if (dia == 28)
            {
                movs.Add(new Mov("nomina", d, 3000m, "debit", "transferencia", "Traspaso a Ahorro — meta mensual", "posted", Ref("TRA"), null));
                movs.Add(new Mov("ahorro", d, 3000m, "credit", "transferencia", "Traspaso desde Nómina — meta mensual", "posted", Ref("TRA"), null));
            }

            // --- Gasto diario variado (2 a 4 movimientos) ---
            var extras = rng.Next(1, 4);
            for (var i = 0; i < extras; i++)
            {
                var pick = rng.NextDouble();
                var cuenta = pick < 0.12 ? "compras" : (pick < 0.18 ? "ahorro" : "nomina");
                if (cuenta == "ahorro" && rng.NextDouble() < 0.5) continue; // menos ruido en ahorro
                switch (rng.Next(10))
                {
                    case 0: movs.Add(new Mov(cuenta, d, Monto(250, 1800), "debit", "super", Pick(supermercados, rng), "posted", Ref("SUP"), "supermarket")); break;
                    case 1: movs.Add(new Mov(cuenta, d, Monto(85, 320), "debit", "comida_rapida", Pick(comidaRapida, rng), "posted", Ref("FAST"), "fast_food")); break;
                    case 2: movs.Add(new Mov(cuenta, d, Monto(280, 1300), "debit", "restaurante", Pick(restaurantes, rng), "posted", Ref("REST"), "restaurant")); break;
                    case 3: movs.Add(new Mov(cuenta, d, Monto(28, 260), "debit", "transporte", Pick(transporte, rng), "posted", Ref("UBER"), "transport")); break;
                    case 4:
                        if (!esFinDeSemana) movs.Add(new Mov(cuenta, d, Monto(400, 950), "debit", "gasolina", Pick(gasolina, rng), "posted", Ref("GAS"), "gas"));
                        break;
                    case 5: movs.Add(new Mov(cuenta, d, Monto(120, 650), "debit", "farmacia", Pick(farmacia, rng), "posted", Ref("FARM"), "drugstore")); break;
                    case 6:
                        if (esFinDeSemana || rng.NextDouble() < 0.4)
                            movs.Add(new Mov(cuenta, d, Monto(160, 700), "debit", "entretenimiento", Pick(entretenimiento, rng), "posted", Ref("ENT"), "entertainment"));
                        break;
                    case 7:
                        if (rng.NextDouble() < 0.35)
                            movs.Add(new Mov(cuenta, d, Monto(200, 1200), "debit", "educacion", Pick(educacion, rng), "posted", Ref("EDU"), "education"));
                        break;
                    case 8:
                        if (rng.NextDouble() < 0.25)
                            movs.Add(new Mov(cuenta, d, Monto(350, 1500), "debit", "medico", Pick(medico, rng), "posted", Ref("MED"), "medical"));
                        break;
                    case 9: movs.Add(new Mov(cuenta, d, Monto(90, 480), "debit", "otro", "Compra en línea Amazon", "posted", Ref("AMZ"), null)); break;
                }
            }
        }

        // --- Estados especiales recientes (pending / failed) para filtros ---
        movs.Add(new Mov("nomina", today, 1450m, "debit", "super", "Walmart Express (en proceso)", "pending", Ref("SUP"), "supermarket"));
        movs.Add(new Mov("nomina", today.AddDays(-1), 380m, "debit", "entretenimiento", "Cinépolis (en proceso)", "pending", Ref("ENT"), "entertainment"));
        movs.Add(new Mov("nomina", today, 95m, "credit", "intereses", "Devolución por promoción", "pending", Ref("DEV"), null));
        movs.Add(new Mov("nomina", today.AddDays(-3), 1200m, "debit", "otro", "Compra declinada por el comercio", "failed", Ref("FALL"), null));
        movs.Add(new Mov("nomina", today.AddDays(-6), 4500m, "debit", "transferencia", "Transferencia devuelta — cuenta destino incorrecta", "failed", Ref("TDEV"), null));

        return movs.OrderBy(m => m.Fecha).ThenBy(m => m.Reference, StringComparer.Ordinal).ToList();
    }

    private static string Pick(string[] opciones, Random rng) => opciones[rng.Next(opciones.Length)];

    // ---------------------------------------------------------------------
    // Transferencias: 5 confirmed externas (ligadas a su transacción del
    // ledger por referencia + ReconciliationMatch), 1 traspaso interno
    // confirmed, 3 pending (simulables con ConfirmAsync), 1 rejected con su
    // transacción failed y match "unmatched".
    // ---------------------------------------------------------------------
    private static void SeedTransfers(
        AppDbContext db, int idUser, Account nomina,
        List<Transaction> transacciones, DateOnly today, DateTime nowUtc)
    {
        var porReferencia = transacciones
            .GroupBy(t => t.Reference)
            .ToDictionary(g => g.Key, g => g.First());

        var transferencias = new List<Transfer>();
        var trSeq = 0;

        DateTime UtcDe(DateOnly fecha, int minutos = 0) =>
            nowUtc.AddDays(-(today.DayNumber - fecha.DayNumber)).AddMinutes(minutos);

        // Externas confirmadas.
        foreach (var (refTx, alias, masked, concepto, metodo) in TransferExternas)
        {
            if (!porReferencia.TryGetValue(refTx, out var tx)) continue;
            trSeq++;
            transferencias.Add(new Transfer
            {
                IdUser = idUser, IdOriginAccount = nomina.IdAccount,
                DestinationAlias = alias, DestinationMasked = masked,
                Amount = tx.Amount, Currency = "MXN", Concept = concepto,
                Status = "confirmed", IdempotencyKey = $"seed-tr-{trSeq:D3}",
                CreatedAt = UtcDe(tx.Date), ConfirmedAt = UtcDe(tx.Date, 3)
            });
        }

        // Traspaso interno confirmado (Nómina -> Ahorro, día 28 del mes pasado).
        trSeq++;
        var fechaInterna = new DateOnly(today.Year, today.Month, 1).AddDays(-1);
        if (fechaInterna.Day != 28) fechaInterna = new DateOnly(fechaInterna.Year, fechaInterna.Month, 28);
        transferencias.Add(new Transfer
        {
            IdUser = idUser, IdOriginAccount = nomina.IdAccount,
            DestinationAlias = "Ahorro (propia)", DestinationMasked = "****4321",
            Amount = 3000m, Currency = "MXN", Concept = "Aporte meta mensual",
            Status = "confirmed", IdempotencyKey = $"seed-tr-{trSeq:D3}",
            CreatedAt = UtcDe(fechaInterna), ConfirmedAt = UtcDe(fechaInterna, 1)
        });

        // Pendientes: listas para el flujo de confirmación de la demo.
        Transfer Pendiente(string alias, string masked, decimal monto, string concepto, DateTime creada)
        {
            trSeq++;
            return new Transfer
            {
                IdUser = idUser, IdOriginAccount = nomina.IdAccount,
                DestinationAlias = alias, DestinationMasked = masked,
                Amount = monto, Currency = "MXN", Concept = concepto,
                Status = "pending", IdempotencyKey = $"seed-tr-{trSeq:D3}",
                CreatedAt = creada, ConfirmedAt = null
            };
        }
        var pendienteMama = Pendiente("Mamá", "****5678", 2000m, "Apoyo", nowUtc.AddHours(-5));
        var pendienteRegalo = Pendiente("Luis (hermano)", "****3377", 1500m, "Regalo de cumpleaños", nowUtc.AddHours(-30));
        var pendienteAporte = Pendiente("Ahorro (propia)", "****4321", 2500m, "Aporte extra meta Viaje a Japón", nowUtc.AddHours(-2));
        transferencias.AddRange([pendienteMama, pendienteRegalo, pendienteAporte]);

        // Rechazada.
        trSeq++;
        var rechazada = new Transfer
        {
            IdUser = idUser, IdOriginAccount = nomina.IdAccount,
            DestinationAlias = "Cuenta incorrecta", DestinationMasked = "****9999",
            Amount = 4500m, Currency = "MXN", Concept = "Pago proveedor",
            Status = "rejected", IdempotencyKey = $"seed-tr-{trSeq:D3}",
            CreatedAt = nowUtc.AddDays(-6), ConfirmedAt = null
        };
        transferencias.Add(rechazada);

        db.Transfers.AddRange(transferencias);
        db.SaveChanges(); // asigna IdTransfer reales

        // Confirmaciones 1:1.
        var confirmations = transferencias.Select(t => new TransferConfirmation
        {
            IdTransfer = t.IdTransfer,
            Method = "app",
            Status = t.Status == "confirmed" ? "confirmed" : t.Status, // pending | rejected
            ConfirmedAt = t.ConfirmedAt
        }).ToList();
        db.TransferConfirmations.AddRange(confirmations);

        // Auditoría de las confirmadas.
        var audits = transferencias.Where(t => t.Status == "confirmed").Select(t => new AuditLog
        {
            IdUser = idUser, Action = "transfer.confirm", Resource = $"transfer:{t.IdTransfer}",
            Result = "ok", RiskLevel = t.Amount > 10000 ? "medium" : "low",
            RedactedPayload = $"amount={t.Amount} dest={t.DestinationMasked}",
            CreatedAt = t.ConfirmedAt ?? t.CreatedAt
        }).ToList();
        db.AuditLogs.AddRange(audits);

        // Conciliación: matched para las externas (la más antigua en
        // "pending" de revisión), unmatched para la rechazada (tx failed).
        // Las transferencias confirmed externas quedaron en transferencias[0..n]
        // en el mismo orden que TransferExternas.
        var matches = new List<ReconciliationMatch>();
        var externas = transferencias.Where(t => t.Status == "confirmed"
            && TransferExternas.Any(e => e.Alias == t.DestinationAlias)).ToList();
        for (var i = 0; i < externas.Count && i < TransferExternas.Length; i++)
        {
            var (refTx, _, _, _, _) = TransferExternas[i];
            if (!porReferencia.TryGetValue(refTx, out var txLiga)) continue;
            var t = externas[i];
            // La más antigua queda en revisión manual (status pending).
            var esRevision = i == 0;
            matches.Add(new ReconciliationMatch
            {
                IdTransfer = t.IdTransfer, IdTransaction = txLiga.IdTransaction,
                Status = esRevision ? "pending" : "matched",
                MatchScore = esRevision ? 0.62f : 0.9f + (i * 0.02f),
                MatchedAt = esRevision ? null : t.ConfirmedAt,
                Notes = esRevision ? "En revisión manual" : "Conciliación automática por monto y referencia"
            });
        }
        var txFallida = transacciones.FirstOrDefault(t => t.Reference.StartsWith("TDEV", StringComparison.Ordinal));
        if (txFallida is not null)
        {
            matches.Add(new ReconciliationMatch
            {
                IdTransfer = rechazada.IdTransfer, IdTransaction = txFallida.IdTransaction,
                Status = "unmatched", MatchScore = 0.3f, MatchedAt = null,
                Notes = "Transferencia devuelta; sin coincidencia en destino"
            });
        }
        db.ReconciliationMatches.AddRange(matches);
        db.SaveChanges();
    }

    // ---------------------------------------------------------------------
    // Presupuestos del MES EN CURSO con CurrentSpent calculado del ledger.
    // Restaurantes queda "exceeded" a propósito (demo de alertas).
    // ---------------------------------------------------------------------
    private static void SeedBudgets(
        AppDbContext db, int idUser, List<Transaction> transacciones,
        Dictionary<string, int> categorias, DateOnly today, DateTime nowUtc, Random rng)
    {
        var mesInicio = new DateOnly(today.Year, today.Month, 1);
        var mesFin = mesInicio.AddMonths(1).AddDays(-1);

        decimal Gastado(string code) =>
            categorias.TryGetValue(code, out var idCat)
                ? transacciones
                    .Where(t => t.Direction == "debit" && t.Status == "posted"
                        && t.IdExpenseCategory == idCat && t.Date >= mesInicio && t.Date <= mesFin)
                    .Sum(t => t.Amount)
                : 0m;

        void Presupuesto(string code, Func<decimal, decimal> limite)
        {
            if (!categorias.TryGetValue(code, out var idCat)) return;
            var gastado = Math.Round(Gastado(code), 2);
            var lim = Math.Round(limite(gastado) / 50m) * 50m;
            if (lim <= 0) lim = 2000m;
            db.Budgets.Add(new Budget
            {
                IdUser = idUser, IdExpenseCategory = idCat,
                Month = today.Month, Year = today.Year,
                AmountLimit = lim, CurrentSpent = gastado,
                StartDate = new DateTime(today.Year, today.Month, 1, 0, 0, 0, DateTimeKind.Utc),
                EndDate = new DateTime(today.Year, today.Month, 1, 0, 0, 0, DateTimeKind.Utc).AddMonths(1).AddTicks(-1),
                Status = gastado >= lim ? "exceeded" : "active",
                CreatedAt = nowUtc.AddMonths(-1), UpdatedAt = nowUtc
            });
        }

        Presupuesto("restaurant", gastado => Math.Max(500m, gastado * 0.8m)); // rebasado a propósito
        Presupuesto("supermarket", gastado => Math.Max(3000m, gastado * (decimal)(1.6 + rng.NextDouble())));
        Presupuesto("transport", gastado => Math.Max(1200m, gastado * (decimal)(1.5 + rng.NextDouble())));
        Presupuesto("entertainment", gastado => Math.Max(900m, gastado * (decimal)(1.4 + rng.NextDouble())));
        Presupuesto("utilities", gastado => Math.Max(1500m, gastado * (decimal)(1.7 + rng.NextDouble())));
        Presupuesto("gas", gastado => Math.Max(1200m, gastado * (decimal)(1.5 + rng.NextDouble())));
        db.SaveChanges();
    }

    // ---------------------------------------------------------------------
    // Estados de cuenta de los 3 meses cerrados anteriores (Nómina), con
    // totales reales del periodo y desglose por categoría de gasto.
    // ---------------------------------------------------------------------
    private static void SeedStatements(
        AppDbContext db, Account nomina, List<Transaction> transacciones,
        DateTime nowUtc, DateOnly today)
    {
        var cierrePrevio = SaldoInicialNomina;
        for (var i = 3; i >= 1; i--)
        {
            var mes = today.AddMonths(-i);
            var corte = DateTime.DaysInMonth(mes.Year, mes.Month);
            var (start, end) = StatementPeriod.Resolve(mes.Year, mes.Month, corte);

            var delPeriodo = transacciones
                .Where(t => t.IdAccount == nomina.IdAccount && t.Status == "posted"
                    && t.Date >= start && t.Date <= end)
                .ToList();

            var credits = delPeriodo.Where(t => t.Direction == "credit").Sum(t => t.Amount);
            var debits = delPeriodo.Where(t => t.Direction == "debit").Sum(t => t.Amount);

            var stmt = new Statement
            {
                IdAccount = nomina.IdAccount, CutOffDay = corte,
                PeriodStart = start, PeriodEnd = end,
                OpeningBalance = cierrePrevio,
                ClosingBalance = Math.Round(cierrePrevio + credits - debits, 2),
                TotalCredits = Math.Round(credits, 2), TotalDebits = Math.Round(debits, 2),
                TransactionCount = delPeriodo.Count,
                AccountType = "debito", Status = "generated",
                GeneratedAt = new DateTime(end.Year, end.Month, end.Day, 0, 0, 0, DateTimeKind.Utc).AddDays(1)
            };
            cierrePrevio = stmt.ClosingBalance;
            db.Statements.Add(stmt);
            db.SaveChanges();

            var desglose = delPeriodo
                .Where(t => t.Direction == "debit" && t.IdExpenseCategory != null)
                .GroupBy(t => t.IdExpenseCategory!.Value)
                .Select(g => new StatementExpense
                {
                    IdStatement = stmt.IdStatement,
                    IdExpenseCategory = g.Key,
                    Amount = Math.Round(g.Sum(t => t.Amount), 2),
                    TransactionCount = g.Count(),
                    FirstTransactionDate = g.Min(t => t.Date),
                    LastTransactionDate = g.Max(t => t.Date)
                });
            db.StatementExpenses.AddRange(desglose);
            db.SaveChanges();
        }
    }

    // ---------------------------------------------------------------------
    // 3 tarjetas de crédito, cada una con su statement del mes anterior.
    // Cortes distintos (15/22/28) para no chocar con el índice único
    // Statement(IdAccount, PeriodStart) — todas se anclan a Nómina.
    // Los pagos mensuales ya están en el ledger (día corte+1).
    // ---------------------------------------------------------------------
    private static void SeedCreditCards(AppDbContext db, int idUser, Account nomina, DateOnly today, DateTime nowUtc)
    {
        foreach (var c in Tarjetas)
        {
            var mes = today.AddMonths(-1);
            var (start, end) = StatementPeriod.Resolve(mes.Year, mes.Month, c.Corte);

            var card = new CreditCard
            {
                IdUser = idUser, CardNumberMasked = c.Masked, CardType = c.Tipo,
                CreditLimit = c.Limite, AvailableCredit = c.Limite,
                InterestRate = (decimal)c.Tasa,
                StatementCutOffDay = c.Corte, PaymentDueDay = c.Pago,
                Status = "active", CreatedAt = nowUtc.AddMonths(-14)
            };
            db.CreditCards.Add(card);
            db.SaveChanges();

            // Mismo cálculo que CreditCardService.GenerateStatementAsync.
            const decimal prevBalance = 0m;
            var interest = Math.Round(Math.Max(0m, prevBalance - c.PagoMensual) * ((decimal)c.Tasa / 100m / 12m), 2, MidpointRounding.AwayFromZero);
            var newBalance = prevBalance + c.ComprasMes + interest - c.PagoMensual;
            var minimum = Math.Round(Math.Max(25m, Math.Max(0m, newBalance) * 0.05m), 2, MidpointRounding.AwayFromZero);
            var dueDay = Math.Min(c.Pago, DateTime.DaysInMonth(end.Year, end.Month));

            var stmt = new Statement
            {
                IdAccount = nomina.IdAccount, CutOffDay = c.Corte,
                PeriodStart = start, PeriodEnd = end,
                OpeningBalance = prevBalance, ClosingBalance = newBalance,
                TotalCredits = c.PagoMensual, TotalDebits = c.ComprasMes + interest,
                TransactionCount = 0,
                AccountType = "credito", Status = "generated",
                GeneratedAt = new DateTime(end.Year, end.Month, end.Day, 0, 0, 0, DateTimeKind.Utc).AddDays(1)
            };
            db.Statements.Add(stmt);
            db.SaveChanges();

            db.CreditCardStatements.Add(new CreditCardStatement
            {
                IdCreditCard = card.IdCreditCard, IdStatement = stmt.IdStatement,
                PreviousBalance = prevBalance, TotalPayments = c.PagoMensual, TotalCredits = c.PagoMensual,
                TotalPurchases = c.ComprasMes, InterestCharges = interest, MinimumPayment = minimum,
                PaymentDueDate = new DateOnly(end.Year, end.Month, dueDay),
                AvailableCredit = c.Limite - Math.Max(0m, newBalance),
                Status = "generated", GeneratedAt = stmt.GeneratedAt
            });
            card.AvailableCredit = c.Limite - Math.Max(0m, newBalance);
            db.SaveChanges();
        }
    }

    // ---------------------------------------------------------------------
    // Sesiones, eventos de memoria y preferencias detectadas variadas.
    // ---------------------------------------------------------------------
    private static void SeedMemoryAndAudit(AppDbContext db, int idUser, DateTime nowUtc)
    {
        var sesiones = new[]
        {
            new Session { IdUser = idUser, StartedAt = nowUtc.AddDays(-2), EndedAt = nowUtc.AddDays(-2).AddMinutes(42), DeviceContext = "web" },
            new Session { IdUser = idUser, StartedAt = nowUtc.AddDays(-1), EndedAt = nowUtc.AddDays(-1).AddMinutes(18), DeviceContext = "android" },
            new Session { IdUser = idUser, StartedAt = nowUtc.AddHours(-3), EndedAt = null, DeviceContext = "web" },
        };
        db.Sessions.AddRange(sesiones);
        db.SaveChanges();

        var detectadas = new[]
        {
            new DetectedPreference { IdUser = idUser, PreferenceType = "fontScale", Value = "1.25", ConfidenceScore = 0.87f, BasedOnEventsCount = 5, UpdatedAt = nowUtc.AddDays(-4) },
            new DetectedPreference { IdUser = idUser, PreferenceType = "highContrast", Value = "true", ConfidenceScore = 0.74f, BasedOnEventsCount = 3, UpdatedAt = nowUtc.AddDays(-3) },
            new DetectedPreference { IdUser = idUser, PreferenceType = "reducedMotion", Value = "true", ConfidenceScore = 0.69f, BasedOnEventsCount = 2, UpdatedAt = nowUtc.AddDays(-1) },
        };
        db.DetectedPreferences.AddRange(detectadas);
        db.SaveChanges();

        db.MemoryEvents.AddRange(
            new MemoryEvent
            {
                IdSession = sesiones[0].IdSession, IdUser = idUser, IdDetectedPreference = detectadas[0].IdDetected,
                EventType = "zoom", Intent = "aumentar-legibilidad", TargetElement = "balance-card",
                RedactedSummary = "usuario amplía texto", SensitivityLevel = "low",
                CreatedAt = nowUtc.AddDays(-2), RetentionUntil = nowUtc.AddDays(88)
            },
            new MemoryEvent
            {
                IdSession = sesiones[0].IdSession, IdUser = idUser, IdDetectedPreference = detectadas[1].IdDetected,
                EventType = "contrast", Intent = "mejorar-contraste", TargetElement = "transactions-table",
                RedactedSummary = "usuario activa alto contraste en tabla", SensitivityLevel = "low",
                CreatedAt = nowUtc.AddDays(-2).AddMinutes(12), RetentionUntil = nowUtc.AddDays(88)
            },
            new MemoryEvent
            {
                IdSession = sesiones[1].IdSession, IdUser = idUser, IdDetectedPreference = detectadas[2].IdDetected,
                EventType = "motion", Intent = "reducir-movimiento", TargetElement = "charts",
                RedactedSummary = "usuario desactiva animaciones de gráficas", SensitivityLevel = "low",
                CreatedAt = nowUtc.AddDays(-1).AddMinutes(5), RetentionUntil = nowUtc.AddDays(89)
            },
            new MemoryEvent
            {
                IdSession = sesiones[1].IdSession, IdUser = idUser, IdDetectedPreference = null,
                EventType = "navigation", Intent = "consultar-movimientos", TargetElement = "bottom-nav",
                RedactedSummary = "usuario navega directo a movimientos", SensitivityLevel = "low",
                CreatedAt = nowUtc.AddDays(-1).AddMinutes(9), RetentionUntil = nowUtc.AddDays(89)
            },
            new MemoryEvent
            {
                IdSession = sesiones[2].IdSession, IdUser = idUser, IdDetectedPreference = null,
                EventType = "voice", Intent = "dictar-mensaje", TargetElement = "chat-composer",
                RedactedSummary = "usuario dicta en vez de escribir", SensitivityLevel = "medium",
                CreatedAt = nowUtc.AddHours(-2), RetentionUntil = nowUtc.AddDays(90)
            },
            new MemoryEvent
            {
                IdSession = sesiones[2].IdSession, IdUser = idUser, IdDetectedPreference = detectadas[0].IdDetected,
                EventType = "zoom", Intent = "aumentar-legibilidad", TargetElement = "plan-panel",
                RedactedSummary = "usuario amplía texto del panel de resultados", SensitivityLevel = "low",
                CreatedAt = nowUtc.AddHours(-1), RetentionUntil = nowUtc.AddDays(90)
            });

        db.AuditLogs.Add(new AuditLog
        {
            IdUser = idUser, Action = "seed", Resource = "database",
            Result = "ok", RiskLevel = "low", RedactedPayload = "seed inicial",
            CreatedAt = nowUtc
        });

        db.SaveChanges();
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
}

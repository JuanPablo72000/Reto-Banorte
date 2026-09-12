using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage.ValueConversion;

namespace BancaAdaptativa.Api.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<User> Users => Set<User>();
    public DbSet<UserProfile> UserProfiles => Set<UserProfile>();
    public DbSet<AccessibilityPreference> AccessibilityPreferences => Set<AccessibilityPreference>();
    public DbSet<Session> Sessions => Set<Session>();
    public DbSet<MemoryEvent> MemoryEvents => Set<MemoryEvent>();
    public DbSet<DetectedPreference> DetectedPreferences => Set<DetectedPreference>();
    public DbSet<Account> Accounts => Set<Account>();
    public DbSet<Transaction> Transactions => Set<Transaction>();
    public DbSet<DailyBalance> DailyBalances => Set<DailyBalance>();
    public DbSet<Transfer> Transfers => Set<Transfer>();
    public DbSet<TransferConfirmation> TransferConfirmations => Set<TransferConfirmation>();
    public DbSet<ReconciliationMatch> ReconciliationMatches => Set<ReconciliationMatch>();
    public DbSet<AuditLog> AuditLogs => Set<AuditLog>();
    public DbSet<ExpenseCategory> ExpenseCategories => Set<ExpenseCategory>();
    public DbSet<Statement> Statements => Set<Statement>();
    public DbSet<StatementExpense> StatementExpenses => Set<StatementExpense>();
    public DbSet<Budget> Budgets => Set<Budget>();
    public DbSet<SavingsGoal> SavingsGoals => Set<SavingsGoal>();
    public DbSet<CreditCard> CreditCards => Set<CreditCard>();
    public DbSet<CreditCardStatement> CreditCardStatements => Set<CreditCardStatement>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // --- UTC: todo DateTime se guarda normalizado a UTC y se lee con Kind=Utc ---
        var dateTimeConverter = new ValueConverter<DateTime, DateTime>(
            v => v.Kind == DateTimeKind.Utc ? v : DateTime.SpecifyKind(v.ToUniversalTime(), DateTimeKind.Utc),
            v => DateTime.SpecifyKind(v, DateTimeKind.Utc));
        var nullableDateTimeConverter = new ValueConverter<DateTime?, DateTime?>(
            v => v == null ? null : (v.Value.Kind == DateTimeKind.Utc ? v : DateTime.SpecifyKind(v.Value.ToUniversalTime(), DateTimeKind.Utc)),
            v => v == null ? null : DateTime.SpecifyKind(v.Value, DateTimeKind.Utc));

        foreach (var entityType in modelBuilder.Model.GetEntityTypes())
        {
            foreach (var property in entityType.GetProperties())
            {
                if (property.ClrType == typeof(DateTime))
                    property.SetValueConverter(dateTimeConverter);
                else if (property.ClrType == typeof(DateTime?))
                    property.SetValueConverter(nullableDateTimeConverter);
            }
        }

        // DateOnly en SQLite se guarda como TEXT yyyy-MM-dd
        var dateOnlyConverter = new ValueConverter<DateOnly, string>(
            v => v.ToString("yyyy-MM-dd"),
            v => DateOnly.ParseExact(v, "yyyy-MM-dd"));

        modelBuilder.Entity<Transaction>().Property(t => t.Date).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<DailyBalance>().Property(d => d.Date).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<Statement>().Property(s => s.PeriodStart).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<Statement>().Property(s => s.PeriodEnd).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<StatementExpense>().Property(e => e.FirstTransactionDate).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<StatementExpense>().Property(e => e.LastTransactionDate).HasConversion(dateOnlyConverter);
        modelBuilder.Entity<CreditCardStatement>().Property(s => s.PaymentDueDate).HasConversion(dateOnlyConverter);

        // --- Relaciones ---
        modelBuilder.Entity<User>().HasIndex(u => u.Email).IsUnique();

        modelBuilder.Entity<User>()
            .HasOne(u => u.UserProfile)
            .WithOne(p => p.User)
            .HasForeignKey<UserProfile>(p => p.IdUser)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<UserProfile>().HasIndex(p => p.IdUser).IsUnique();

        modelBuilder.Entity<User>()
            .HasOne(u => u.AccessibilityPreference)
            .WithOne(p => p.User)
            .HasForeignKey<AccessibilityPreference>(p => p.IdUser)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<AccessibilityPreference>().HasIndex(p => p.IdUser).IsUnique();

        modelBuilder.Entity<Session>()
            .HasOne(s => s.User)
            .WithMany(u => u.Sessions)
            .HasForeignKey(s => s.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<MemoryEvent>()
            .HasOne(m => m.Session)
            .WithMany(s => s.MemoryEvents)
            .HasForeignKey(m => m.IdSession)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<MemoryEvent>()
            .HasOne(m => m.User)
            .WithMany(u => u.MemoryEvents)
            .HasForeignKey(m => m.IdUser)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<MemoryEvent>()
            .HasOne(m => m.DetectedPreference)
            .WithMany(d => d.MemoryEvents)
            .HasForeignKey(m => m.IdDetectedPreference)
            .IsRequired(false)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<DetectedPreference>()
            .HasOne(d => d.User)
            .WithMany(u => u.DetectedPreferences)
            .HasForeignKey(d => d.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Account>()
            .HasOne(a => a.User)
            .WithMany(u => u.Accounts)
            .HasForeignKey(a => a.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Transaction>()
            .HasOne(t => t.Account)
            .WithMany(a => a.Transactions)
            .HasForeignKey(t => t.IdAccount)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<DailyBalance>()
            .HasOne(d => d.Account)
            .WithMany(a => a.DailyBalances)
            .HasForeignKey(d => d.IdAccount)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<DailyBalance>().HasIndex(d => new { d.IdAccount, d.Date }).IsUnique();

        modelBuilder.Entity<Transfer>()
            .HasOne(t => t.User)
            .WithMany(u => u.Transfers)
            .HasForeignKey(t => t.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<Transfer>()
            .HasOne(t => t.OriginAccount)
            .WithMany(a => a.Transfers)
            .HasForeignKey(t => t.IdOriginAccount)
            .OnDelete(DeleteBehavior.Restrict);
        modelBuilder.Entity<Transfer>().HasIndex(t => t.IdempotencyKey).IsUnique();

        modelBuilder.Entity<TransferConfirmation>()
            .HasOne(c => c.Transfer)
            .WithMany(t => t.Confirmations)
            .HasForeignKey(c => c.IdTransfer)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<ReconciliationMatch>()
            .HasOne(r => r.Transfer)
            .WithOne(t => t.ReconciliationMatch)
            .HasForeignKey<ReconciliationMatch>(r => r.IdTransfer)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<ReconciliationMatch>().HasIndex(r => r.IdTransfer).IsUnique();

        modelBuilder.Entity<ReconciliationMatch>()
            .HasOne(r => r.Transaction)
            .WithOne(t => t.ReconciliationMatch)
            .HasForeignKey<ReconciliationMatch>(r => r.IdTransaction)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<ReconciliationMatch>().HasIndex(r => r.IdTransaction).IsUnique();

        modelBuilder.Entity<AuditLog>()
            .HasOne(a => a.User)
            .WithMany(u => u.AuditLogs)
            .HasForeignKey(a => a.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        // --- Estados de cuenta y finanzas personales ---
        modelBuilder.Entity<ExpenseCategory>().HasIndex(c => c.Code).IsUnique();

        modelBuilder.Entity<Transaction>()
            .HasOne(t => t.ExpenseCategory)
            .WithMany(c => c.Transactions)
            .HasForeignKey(t => t.IdExpenseCategory)
            .IsRequired(false)
            .OnDelete(DeleteBehavior.SetNull);

        modelBuilder.Entity<Statement>()
            .HasOne(s => s.Account)
            .WithMany(a => a.Statements)
            .HasForeignKey(s => s.IdAccount)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<Statement>().HasIndex(s => new { s.IdAccount, s.PeriodStart }).IsUnique();

        modelBuilder.Entity<StatementExpense>()
            .HasOne(e => e.Statement)
            .WithMany(s => s.StatementExpenses)
            .HasForeignKey(e => e.IdStatement)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<StatementExpense>()
            .HasOne(e => e.ExpenseCategory)
            .WithMany(c => c.StatementExpenses)
            .HasForeignKey(e => e.IdExpenseCategory)
            .OnDelete(DeleteBehavior.Restrict);
        modelBuilder.Entity<StatementExpense>().HasIndex(e => new { e.IdStatement, e.IdExpenseCategory }).IsUnique();

        modelBuilder.Entity<Budget>()
            .HasOne(b => b.User)
            .WithMany(u => u.Budgets)
            .HasForeignKey(b => b.IdUser)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<Budget>()
            .HasOne(b => b.ExpenseCategory)
            .WithMany(c => c.Budgets)
            .HasForeignKey(b => b.IdExpenseCategory)
            .OnDelete(DeleteBehavior.Restrict);
        modelBuilder.Entity<Budget>().HasIndex(b => new { b.IdUser, b.IdExpenseCategory, b.Month, b.Year }).IsUnique();

        modelBuilder.Entity<SavingsGoal>()
            .HasOne(g => g.User)
            .WithMany(u => u.SavingsGoals)
            .HasForeignKey(g => g.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CreditCard>()
            .HasOne(c => c.User)
            .WithMany(u => u.CreditCards)
            .HasForeignKey(c => c.IdUser)
            .OnDelete(DeleteBehavior.Cascade);

        modelBuilder.Entity<CreditCardStatement>()
            .HasOne(s => s.CreditCard)
            .WithMany(c => c.CreditCardStatements)
            .HasForeignKey(s => s.IdCreditCard)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<CreditCardStatement>()
            .HasOne(s => s.Statement)
            .WithOne(s => s.CreditCardStatement)
            .HasForeignKey<CreditCardStatement>(s => s.IdStatement)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<CreditCardStatement>().HasIndex(s => s.IdStatement).IsUnique();
    }
}

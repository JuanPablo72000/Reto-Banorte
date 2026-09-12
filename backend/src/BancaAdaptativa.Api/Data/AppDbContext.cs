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
    }
}

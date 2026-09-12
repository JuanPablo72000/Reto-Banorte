using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class User
{
    [Key]
    public int IdUser { get; set; }

    [Required, MaxLength(120)]
    public string Name { get; set; } = string.Empty;

    [Required, MaxLength(160)]
    public string Email { get; set; } = string.Empty;

    // Nunca se expone en DTOs. Hash BCrypt.
    [Required]
    public string PasswordHash { get; set; } = string.Empty;

    [MaxLength(10)]
    public string Locale { get; set; } = "es-MX";

    [MaxLength(20)]
    public string Status { get; set; } = "active";

    public DateTime CreatedAt { get; set; }

    public UserProfile? UserProfile { get; set; }
    public AccessibilityPreference? AccessibilityPreference { get; set; }

    public ICollection<Account> Accounts { get; set; } = new List<Account>();
    public ICollection<Session> Sessions { get; set; } = new List<Session>();
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
    public ICollection<DetectedPreference> DetectedPreferences { get; set; } = new List<DetectedPreference>();
    public ICollection<Transfer> Transfers { get; set; } = new List<Transfer>();
    public ICollection<AuditLog> AuditLogs { get; set; } = new List<AuditLog>();
    public ICollection<Budget> Budgets { get; set; } = new List<Budget>();
    public ICollection<SavingsGoal> SavingsGoals { get; set; } = new List<SavingsGoal>();
    public ICollection<CreditCard> CreditCards { get; set; } = new List<CreditCard>();
}

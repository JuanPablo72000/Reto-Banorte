using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class MemoryEvent
{
    [Key]
    public int IdEvent { get; set; }
    public int IdSession { get; set; }
    public int IdUser { get; set; }
    public int? IdDetectedPreference { get; set; }

    [MaxLength(60)]
    public string EventType { get; set; } = string.Empty;
    [MaxLength(120)]
    public string Intent { get; set; } = string.Empty;
    [MaxLength(120)]
    public string TargetElement { get; set; } = string.Empty;
    [MaxLength(500)]
    public string RedactedSummary { get; set; } = string.Empty;
    [MaxLength(10)]
    public string SensitivityLevel { get; set; } = "low";

    public DateTime CreatedAt { get; set; }
    public DateTime? RetentionUntil { get; set; }

    public Session Session { get; set; } = null!;
    public User User { get; set; } = null!;
    public DetectedPreference? DetectedPreference { get; set; }
}

using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class AuditLog
{
    [Key]
    public int IdLog { get; set; }
    public int IdUser { get; set; }

    [MaxLength(60)]
    public string Action { get; set; } = string.Empty;
    [MaxLength(60)]
    public string Resource { get; set; } = string.Empty;
    [MaxLength(20)]
    public string Result { get; set; } = string.Empty;
    [MaxLength(10)]
    public string RiskLevel { get; set; } = "low";
    [MaxLength(1000)]
    public string RedactedPayload { get; set; } = string.Empty;

    public DateTime CreatedAt { get; set; }

    public User User { get; set; } = null!;
}

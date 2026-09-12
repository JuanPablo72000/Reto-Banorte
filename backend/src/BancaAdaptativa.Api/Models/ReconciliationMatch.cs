using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class ReconciliationMatch
{
    [Key]
    public int IdMatch { get; set; }
    public int IdTransfer { get; set; }
    public int IdTransaction { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "pending";
    public float MatchScore { get; set; }

    public DateTime? MatchedAt { get; set; }

    [MaxLength(300)]
    public string Notes { get; set; } = string.Empty;

    public Transfer Transfer { get; set; } = null!;
    public Transaction Transaction { get; set; } = null!;
}

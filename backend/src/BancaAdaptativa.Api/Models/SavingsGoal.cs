using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class SavingsGoal
{
    [Key]
    public int IdGoal { get; set; }
    public int IdUser { get; set; }

    [MaxLength(100)]
    public string Name { get; set; } = string.Empty;

    [Column(TypeName = "decimal(18,2)")]
    public decimal TargetAmount { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal CurrentAmount { get; set; }

    public DateTime TargetDate { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "active";

    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
}

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class DailyBalance
{
    [Key]
    public int IdBalance { get; set; }
    public int IdAccount { get; set; }

    public DateOnly Date { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal OpeningBalance { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal Income { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal Expenses { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal ClosingBalance { get; set; }

    public Account Account { get; set; } = null!;
}

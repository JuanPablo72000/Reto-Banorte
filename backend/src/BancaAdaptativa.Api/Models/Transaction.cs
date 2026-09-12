using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class Transaction
{
    [Key]
    public int IdTransaction { get; set; }
    public int IdAccount { get; set; }

    public DateOnly Date { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal Amount { get; set; }

    [MaxLength(10)]
    public string Direction { get; set; } = string.Empty;
    [MaxLength(40)]
    public string Category { get; set; } = string.Empty;
    [MaxLength(200)]
    public string Description { get; set; } = string.Empty;
    [MaxLength(20)]
    public string Status { get; set; } = string.Empty;
    [MaxLength(60)]
    public string Reference { get; set; } = string.Empty;

    public int? IdExpenseCategory { get; set; }

    public Account Account { get; set; } = null!;
    public ReconciliationMatch? ReconciliationMatch { get; set; }
    public ExpenseCategory? ExpenseCategory { get; set; }
}

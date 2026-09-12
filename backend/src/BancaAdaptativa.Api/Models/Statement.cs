using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class Statement
{
    [Key]
    public int IdStatement { get; set; }
    public int IdAccount { get; set; }

    public int CutOffDay { get; set; }
    public DateOnly PeriodStart { get; set; }
    public DateOnly PeriodEnd { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal OpeningBalance { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal ClosingBalance { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalCredits { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalDebits { get; set; }

    public int TransactionCount { get; set; }

    [MaxLength(30)]
    public string AccountType { get; set; } = string.Empty;

    [MaxLength(20)]
    public string Status { get; set; } = "generated";

    public DateTime GeneratedAt { get; set; }

    public Account Account { get; set; } = null!;
    public ICollection<StatementExpense> StatementExpenses { get; set; } = new List<StatementExpense>();
    public CreditCardStatement? CreditCardStatement { get; set; }
}

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class StatementExpense
{
    [Key]
    public int IdStatementExpense { get; set; }
    public int IdStatement { get; set; }
    public int IdExpenseCategory { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal Amount { get; set; }
    public int TransactionCount { get; set; }
    public DateOnly? FirstTransactionDate { get; set; }
    public DateOnly? LastTransactionDate { get; set; }

    public Statement Statement { get; set; } = null!;
    public ExpenseCategory ExpenseCategory { get; set; } = null!;
}

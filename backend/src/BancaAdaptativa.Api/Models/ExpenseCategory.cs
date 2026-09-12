using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class ExpenseCategory
{
    [Key]
    public int IdCategory { get; set; }

    [MaxLength(60)]
    public string Name { get; set; } = string.Empty;

    [MaxLength(30)]
    public string Code { get; set; } = string.Empty;

    [MaxLength(40)]
    public string Icon { get; set; } = string.Empty;

    public bool IsDefault { get; set; }
    public int SortOrder { get; set; }

    public ICollection<Transaction> Transactions { get; set; } = new List<Transaction>();
    public ICollection<StatementExpense> StatementExpenses { get; set; } = new List<StatementExpense>();
    public ICollection<Budget> Budgets { get; set; } = new List<Budget>();
}

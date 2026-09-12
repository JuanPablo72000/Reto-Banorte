using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class Budget
{
    [Key]
    public int IdBudget { get; set; }
    public int IdUser { get; set; }
    public int IdExpenseCategory { get; set; }

    public int Month { get; set; }
    public int Year { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal AmountLimit { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal CurrentSpent { get; set; }

    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "active";

    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
    public ExpenseCategory ExpenseCategory { get; set; } = null!;
}

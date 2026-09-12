using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class CreditCardStatement
{
    [Key]
    public int IdCreditCardStatement { get; set; }
    public int IdCreditCard { get; set; }
    public int IdStatement { get; set; }

    [Column(TypeName = "decimal(18,2)")]
    public decimal PreviousBalance { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalPayments { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalCredits { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal TotalPurchases { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal InterestCharges { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal MinimumPayment { get; set; }
    public DateOnly PaymentDueDate { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal AvailableCredit { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "generated";

    public DateTime GeneratedAt { get; set; }

    public CreditCard CreditCard { get; set; } = null!;
    public Statement Statement { get; set; } = null!;
}

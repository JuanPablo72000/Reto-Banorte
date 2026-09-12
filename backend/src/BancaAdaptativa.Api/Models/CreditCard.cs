using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class CreditCard
{
    [Key]
    public int IdCreditCard { get; set; }
    public int IdUser { get; set; }

    [MaxLength(20)]
    public string CardNumberMasked { get; set; } = string.Empty;

    [MaxLength(20)]
    public string CardType { get; set; } = string.Empty;

    [Column(TypeName = "decimal(18,2)")]
    public decimal CreditLimit { get; set; }
    [Column(TypeName = "decimal(18,2)")]
    public decimal AvailableCredit { get; set; }
    public decimal InterestRate { get; set; }

    public int StatementCutOffDay { get; set; }
    public int PaymentDueDay { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "active";

    public DateTime CreatedAt { get; set; }

    public User User { get; set; } = null!;
    public ICollection<CreditCardStatement> CreditCardStatements { get; set; } = new List<CreditCardStatement>();
}

using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class Account
{
    [Key]
    public int IdAccount { get; set; }
    public int IdUser { get; set; }

    [MaxLength(30)]
    public string AccountType { get; set; } = string.Empty;
    [MaxLength(60)]
    public string Alias { get; set; } = string.Empty;
    [MaxLength(20)]
    public string MaskedNumber { get; set; } = string.Empty;
    [MaxLength(5)]
    public string Currency { get; set; } = "MXN";

    [Column(TypeName = "decimal(18,2)")]
    public decimal Balance { get; set; }

    [MaxLength(20)]
    public string Status { get; set; } = "active";
    public DateTime CreatedAt { get; set; }

    public User User { get; set; } = null!;

    public ICollection<Transaction> Transactions { get; set; } = new List<Transaction>();
    public ICollection<DailyBalance> DailyBalances { get; set; } = new List<DailyBalance>();
    public ICollection<Transfer> Transfers { get; set; } = new List<Transfer>();
    public ICollection<Statement> Statements { get; set; } = new List<Statement>();
}

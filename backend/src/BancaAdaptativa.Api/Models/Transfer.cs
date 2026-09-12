using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace BancaAdaptativa.Api.Models;

public class Transfer
{
    [Key]
    public int IdTransfer { get; set; }
    public int IdUser { get; set; }
    public int IdOriginAccount { get; set; }

    [MaxLength(60)]
    public string DestinationAlias { get; set; } = string.Empty;
    [MaxLength(20)]
    public string DestinationMasked { get; set; } = string.Empty;

    [Column(TypeName = "decimal(18,2)")]
    public decimal Amount { get; set; }
    [MaxLength(5)]
    public string Currency { get; set; } = "MXN";
    [MaxLength(140)]
    public string Concept { get; set; } = string.Empty;
    [MaxLength(20)]
    public string Status { get; set; } = "pending";

    [MaxLength(80)]
    public string IdempotencyKey { get; set; } = Guid.NewGuid().ToString();

    public DateTime? ConfirmedAt { get; set; }

    public User User { get; set; } = null!;
    public Account OriginAccount { get; set; } = null!;

    public ICollection<TransferConfirmation> Confirmations { get; set; } = new List<TransferConfirmation>();
    public ReconciliationMatch? ReconciliationMatch { get; set; }
}

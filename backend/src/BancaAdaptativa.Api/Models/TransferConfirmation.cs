using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class TransferConfirmation
{
    [Key]
    public int IdConfirmation { get; set; }
    public int IdTransfer { get; set; }

    [MaxLength(30)]
    public string Method { get; set; } = string.Empty;
    [MaxLength(20)]
    public string Status { get; set; } = "pending";

    public DateTime? ConfirmedAt { get; set; }

    public Transfer Transfer { get; set; } = null!;
}

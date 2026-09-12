using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class UserProfile
{
    [Key]
    public int IdProfile { get; set; }
    public int IdUser { get; set; }
    public int Age { get; set; }

    [MaxLength(60)]
    public string DisabilityType { get; set; } = string.Empty;

    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
}

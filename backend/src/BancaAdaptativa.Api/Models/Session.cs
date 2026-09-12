using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class Session
{
    [Key]
    public int IdSession { get; set; }
    public int IdUser { get; set; }

    public DateTime StartedAt { get; set; }
    public DateTime? EndedAt { get; set; }

    [MaxLength(200)]
    public string DeviceContext { get; set; } = string.Empty;

    public User User { get; set; } = null!;
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
}

using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class DetectedPreference
{
    [Key]
    public int IdDetected { get; set; }
    public int IdUser { get; set; }

    [MaxLength(60)]
    public string PreferenceType { get; set; } = string.Empty;
    [MaxLength(200)]
    public string Value { get; set; } = string.Empty;

    public float ConfidenceScore { get; set; }
    public int BasedOnEventsCount { get; set; }

    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
    public ICollection<MemoryEvent> MemoryEvents { get; set; } = new List<MemoryEvent>();
}

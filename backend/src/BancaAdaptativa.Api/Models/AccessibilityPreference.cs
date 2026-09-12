using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Models;

public class AccessibilityPreference
{
    [Key]
    public int IdPreference { get; set; }
    public int IdUser { get; set; }

    public float FontScale { get; set; } = 1.0f;
    public bool HighContrast { get; set; }
    public bool DarkMode { get; set; }
    public bool ReducedMotion { get; set; }
    public bool LargeTargets { get; set; }
    public bool PlainLanguage { get; set; }

    public DateTime UpdatedAt { get; set; }

    public User User { get; set; } = null!;
}

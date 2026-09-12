using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.Preferences;

public record AccessibilityPreferenceResponse(
    int IdPreference, float FontScale, bool HighContrast, bool DarkMode,
    bool ReducedMotion, bool LargeTargets, bool PlainLanguage, DateTime UpdatedAt);

public record UpdatePreferencesRequest(
    [Range(0.5, 3.0)] float? FontScale,
    bool? HighContrast, bool? DarkMode, bool? ReducedMotion,
    bool? LargeTargets, bool? PlainLanguage);

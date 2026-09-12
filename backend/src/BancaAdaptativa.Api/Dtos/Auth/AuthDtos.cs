using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.Auth;

public record RegisterRequest(
    [Required, MaxLength(120)] string Name,
    [Required, EmailAddress, MaxLength(160)] string Email,
    [Required, MinLength(8), MaxLength(100)] string Password,
    [MaxLength(10)] string Locale = "es-MX");

public record LoginRequest(
    [Required, EmailAddress] string Email,
    [Required] string Password);

public record AuthResponse(string Token, DateTime ExpiresAtUtc, UserDto User);

public record UserDto(int IdUser, string Name, string Email, string Locale, string Status, DateTime CreatedAt);

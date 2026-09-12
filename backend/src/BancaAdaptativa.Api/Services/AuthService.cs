using System.IdentityModel.Tokens.Jwt;
using System.Security.Claims;
using System.Text;
using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Auth;
using BancaAdaptativa.Api.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;

namespace BancaAdaptativa.Api.Services;

public interface IAuthService
{
    Task<AuthResponse> RegisterAsync(RegisterRequest req, CancellationToken ct = default);
    Task<AuthResponse> LoginAsync(LoginRequest req, CancellationToken ct = default);
}

public class AuthService(AppDbContext db, TimeProvider timeProvider, IConfiguration config) : IAuthService
{
    public async Task<AuthResponse> RegisterAsync(RegisterRequest req, CancellationToken ct = default)
    {
        var email = req.Email.Trim().ToLowerInvariant();
        if (await db.Users.AnyAsync(u => u.Email == email, ct))
            throw new InvalidOperationException("EMAIL_TAKEN");

        var nowUtc = timeProvider.GetUtcNow().UtcDateTime;
        var user = new User
        {
            Name = req.Name.Trim(),
            Email = email,
            PasswordHash = BCrypt.Net.BCrypt.HashPassword(req.Password),
            Locale = string.IsNullOrWhiteSpace(req.Locale) ? "es-MX" : req.Locale,
            Status = "active",
            CreatedAt = nowUtc
        };
        db.Users.Add(user);
        await db.SaveChangesAsync(ct);

        db.AccessibilityPreferences.Add(new AccessibilityPreference { IdUser = user.IdUser, UpdatedAt = nowUtc });
        await db.SaveChangesAsync(ct);

        return BuildResponse(user, nowUtc);
    }

    public async Task<AuthResponse> LoginAsync(LoginRequest req, CancellationToken ct = default)
    {
        var email = req.Email.Trim().ToLowerInvariant();
        var user = await db.Users.FirstOrDefaultAsync(u => u.Email == email, ct);
        if (user is null || !BCrypt.Net.BCrypt.Verify(req.Password, user.PasswordHash))
            throw new UnauthorizedAccessException("INVALID_CREDENTIALS");

        return BuildResponse(user, timeProvider.GetUtcNow().UtcDateTime);
    }

    private AuthResponse BuildResponse(User user, DateTime nowUtc)
    {
        var key = config["Jwt:Key"] ?? Environment.GetEnvironmentVariable("JWT_KEY")
            ?? throw new InvalidOperationException("JWT_KEY no configurado. Define env JWT_KEY o Jwt:Key.");
        var issuer = config["Jwt:Issuer"] ?? "banca-adaptativa";
        var audience = config["Jwt:Audience"] ?? "banca-clients";
        var minutes = int.TryParse(config["Jwt:ExpiresMinutes"], out var m) ? m : 60;
        var expires = nowUtc.AddMinutes(minutes);

        var handler = new JwtSecurityTokenHandler();
        var descriptor = new SecurityTokenDescriptor
        {
            Subject = new ClaimsIdentity([
                new Claim(JwtRegisteredClaimNames.Sub, user.IdUser.ToString()),
                new Claim(JwtRegisteredClaimNames.Email, user.Email),
                new Claim(ClaimTypes.NameIdentifier, user.IdUser.ToString()),
            ]),
            Expires = expires,
            Issuer = issuer,
            Audience = audience,
            SigningCredentials = new SigningCredentials(
                new SymmetricSecurityKey(Encoding.UTF8.GetBytes(key)), SecurityAlgorithms.HmacSha256Signature)
        };
        var token = handler.WriteToken(handler.CreateToken(descriptor));
        return new AuthResponse(token, DateTime.SpecifyKind(expires, DateTimeKind.Utc),
            new UserDto(user.IdUser, user.Name, user.Email, user.Locale, user.Status,
                DateTime.SpecifyKind(user.CreatedAt, DateTimeKind.Utc)));
    }
}

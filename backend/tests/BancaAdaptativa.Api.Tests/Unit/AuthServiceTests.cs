using System.IdentityModel.Tokens.Jwt;
using System.Text;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using BancaAdaptativa.Api.Dtos.Auth;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.IdentityModel.Tokens;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes: quitar ToLowerInvariant/Trim, quitar EMAIL_TAKEN, aceptar password wrong,
/// quitar CreatedAt UTC, quitar expiración JWT.
/// </summary>
public class AuthServiceTests
{
    private static IConfiguration Config(string minutes = "60") =>
        new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["Jwt:Key"] = "test-key-32-chars-minimo-1234567890",
            ["Jwt:Issuer"] = "banca-adaptativa",
            ["Jwt:Audience"] = "banca-clients",
            ["Jwt:ExpiresMinutes"] = minutes,
        }).Build();

    [Fact]
    public async Task Register_NormalizaEmail_YCreatedAtUtc()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());

        var r = await svc.RegisterAsync(new RegisterRequest("Ana", "  ANA@Mail.MX ", "Password123!", "es-MX"));

        Assert.Equal("ana@mail.mx", r.User.Email); // mata: quitar Trim/ToLowerInvariant
        Assert.Equal(TestDb.FixedNow.UtcDateTime, r.User.CreatedAt);
        Assert.Equal(DateTimeKind.Utc, r.User.CreatedAt.Kind);
        Assert.False(string.IsNullOrWhiteSpace(r.Token));
    }

    [Fact]
    public async Task Register_EmailDuplicado_LanzaEmailTaken()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());
        await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            svc.RegisterAsync(new RegisterRequest("B", "A@A.MX", "Password123!")));
        Assert.Equal("EMAIL_TAKEN", ex.Message); // mata: quitar AnyAsync check
    }

    [Fact]
    public async Task Login_PasswordIncorrecto_Lanza()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());
        await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        var ex = await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            svc.LoginAsync(new LoginRequest("a@a.mx", "wrong"))); // mata: quitar BCrypt.Verify
        Assert.Equal("INVALID_CREDENTIALS", ex.Message); // mata #830
    }

    [Fact]
    public async Task Login_ExpiraEn60Minutos()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());
        await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        var r = await svc.LoginAsync(new LoginRequest("A@A.MX", "Password123!"));

        Assert.Equal(TestDb.FixedNow.UtcDateTime.AddMinutes(60), r.ExpiresAtUtc);
    }

    [Fact] // mata #812-817: Locale null/vacío -> es-MX, explícito se respeta
    public async Task Register_Locale_DefaultYExplicito()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());

        var def = await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!", null!));
        Assert.Equal("es-MX", def.User.Locale);

        var exp = await svc.RegisterAsync(new RegisterRequest("B", "b@b.mx", "Password123!", "en-US"));
        Assert.Equal("en-US", exp.User.Locale);
    }

    [Fact] // mata #818 (Status) y #822 (2do SaveChanges: preferencias persistidas)
    public async Task Register_StatusActive_YCreaPreferencias()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());

        var r = await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        Assert.Equal("active", r.User.Status);
        t.Db.ChangeTracker.Clear();
        var prefs = await t.Db.AccessibilityPreferences
            .AsNoTracking().SingleOrDefaultAsync(p => p.IdUser == r.User.IdUser);
        Assert.NotNull(prefs);
        Assert.Equal(TestDb.FixedNow.UtcDateTime, prefs!.UpdatedAt);
    }

    [Fact] // mata #844: Jwt:ExpiresMinutes distinto de 60
    public async Task Login_ExpiraSegunConfig()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config("120"));
        await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        var r = await svc.LoginAsync(new LoginRequest("a@a.mx", "Password123!"));

        Assert.Equal(TestDb.FixedNow.UtcDateTime.AddMinutes(120), r.ExpiresAtUtc);
    }

    [Fact] // mata #832/#833/#836/#837/#839/#840: firma, issuer y audience salen de la config
    public async Task Login_Token_ValidaFirmaYClaimsDeConfig()
    {
        using var t = new TestDb();
        var svc = new AuthService(t.Db, t.Time, Config());
        await svc.RegisterAsync(new RegisterRequest("A", "a@a.mx", "Password123!"));

        var r = await svc.LoginAsync(new LoginRequest("a@a.mx", "Password123!"));

        var handler = new JwtSecurityTokenHandler();
        var principal = handler.ValidateToken(r.Token, new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidateAudience = true,
            ValidateLifetime = true,
            ValidateIssuerSigningKey = true,
            ValidIssuer = "banca-adaptativa",
            ValidAudience = "banca-clients",
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes("test-key-32-chars-minimo-1234567890")),
            ClockSkew = TimeSpan.FromMinutes(5),
        }, out _);
        Assert.Equal("a@a.mx", principal.FindFirst(System.Security.Claims.ClaimTypes.Email)!.Value);
    }

    [Fact] // mata #834/#835: sin Jwt:Key ni env -> lanza con mensaje
    public async Task Register_SinJwtKey_Lanza()
    {
        using var t = new TestDb();
        var prev = Environment.GetEnvironmentVariable("JWT_KEY");
        Environment.SetEnvironmentVariable("JWT_KEY", null);
        try
        {
            var cfg = new ConfigurationBuilder()
                .AddInMemoryCollection(new Dictionary<string, string?>()).Build();
            var svc = new AuthService(t.Db, t.Time, cfg);

            var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
                svc.RegisterAsync(new RegisterRequest("A", "nokey@a.mx", "Password123!")));
            Assert.Contains("JWT_KEY", ex.Message);
        }
        finally
        {
            Environment.SetEnvironmentVariable("JWT_KEY", prev);
        }
    }
}

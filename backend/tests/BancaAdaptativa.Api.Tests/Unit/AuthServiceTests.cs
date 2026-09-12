using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using BancaAdaptativa.Api.Dtos.Auth;
using Microsoft.Extensions.Configuration;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes: quitar ToLowerInvariant/Trim, quitar EMAIL_TAKEN, aceptar password wrong,
/// quitar CreatedAt UTC, quitar expiración JWT.
/// </summary>
public class AuthServiceTests
{
    private static IConfiguration Config() =>
        new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["Jwt:Key"] = "test-key-32-chars-minimo-1234567890",
            ["Jwt:Issuer"] = "banca-adaptativa",
            ["Jwt:Audience"] = "banca-clients",
            ["Jwt:ExpiresMinutes"] = "60",
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

        await Assert.ThrowsAsync<UnauthorizedAccessException>(() =>
            svc.LoginAsync(new LoginRequest("a@a.mx", "wrong"))); // mata: quitar BCrypt.Verify
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
}

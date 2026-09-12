using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

public class AuthFlowTests
{
    [Fact]
    public async Task Register_Login_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();
        var email = $"u{Guid.NewGuid():N}@t.mx";

        var reg = await client.PostAsJsonAsync("/auth/register",
            new { name = "Test", email, password = "Password123!", locale = "es-MX" });
        Assert.Equal(HttpStatusCode.Created, reg.StatusCode);
        var regBody = await reg.Content.ReadFromJsonAsync<AuthDto>();
        Assert.False(string.IsNullOrWhiteSpace(regBody!.token));

        var login = await client.PostAsJsonAsync("/auth/login",
            new { email, password = "Password123!" });
        Assert.Equal(HttpStatusCode.OK, login.StatusCode);

        // email duplicado (case-insensitive) => 409: mata mutante ToLowerInvariant
        var dup = await client.PostAsJsonAsync("/auth/register",
            new { name = "X", email = email.ToUpperInvariant(), password = "Password123!" });
        Assert.Equal(HttpStatusCode.Conflict, dup.StatusCode);

        // password mal => 401: mata mutante BCrypt.Verify
        var bad = await client.PostAsJsonAsync("/auth/login",
            new { email, password = "wrong-pass" });
        Assert.Equal(HttpStatusCode.Unauthorized, bad.StatusCode);
    }

    [Fact]
    public async Task UsersMe_ConToken_DevuelveUsuario()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();
        var token = await LoginDemoAsync(client);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        var me = await client.GetAsync("/users/me");
        Assert.Equal(HttpStatusCode.OK, me.StatusCode);
        var body = await me.Content.ReadFromJsonAsync<UserDto>();
        Assert.Equal("demo@banorte.mx", body!.email);
    }

    public static async Task<string> LoginDemoAsync(HttpClient client)
    {
        var login = await client.PostAsJsonAsync("/auth/login",
            new { email = "demo@banorte.mx", password = "Demo123!" });
        login.EnsureSuccessStatusCode();
        var body = await login.Content.ReadFromJsonAsync<AuthDto>();
        return body!.token;
    }

    private sealed record AuthDto(string token, DateTime expiresAtUtc, UserDto user);
    private sealed record UserDto(int idUser, string name, string email, string locale, string status, DateTime createdAt);
}

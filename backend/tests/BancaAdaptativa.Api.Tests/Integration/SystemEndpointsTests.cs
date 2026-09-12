using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

public class SystemEndpointsTests
{
    [Fact]
    public async Task ServerTime_DevuelveUtcDelTimeProvider()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();

        var res = await client.GetAsync("/server-time");
        Assert.Equal(HttpStatusCode.OK, res.StatusCode);
        var body = await res.Content.ReadFromJsonAsync<ServerTimeDto>();
        Assert.NotNull(body);
        // FakeTime congelado: mata mutante que use DateTime.Now/UtcNow directo
        var expected = f.FakeTime.GetUtcNow();
        Assert.Equal(expected.UtcDateTime, body!.serverTimeUtc);
        Assert.Equal(expected.ToUnixTimeMilliseconds(), body.unixMilliseconds);
    }

    [Fact]
    public async Task Health_DevuelveOk()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();
        var res = await client.GetAsync("/health");
        Assert.Equal(HttpStatusCode.OK, res.StatusCode);
        var body = await res.Content.ReadFromJsonAsync<HealthDto>();
        Assert.Equal("ok", body!.status);
    }

    [Fact]
    public async Task RutaProtegida_SinToken_Retorna401()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();
        Assert.Equal(HttpStatusCode.Unauthorized, (await client.GetAsync("/accounts")).StatusCode);
    }

    private sealed record ServerTimeDto(DateTime serverTimeUtc, long unixMilliseconds);
    private sealed record HealthDto(string status, DateTime serverTimeUtc, string dbPath);
}

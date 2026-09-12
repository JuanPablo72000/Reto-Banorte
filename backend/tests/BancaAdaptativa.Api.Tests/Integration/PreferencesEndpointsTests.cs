using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

public class PreferencesEndpointsTests
{
    [Fact]
    public async Task GetPut_Preferences_ActualizaUpdatedAt()
    {
        using var f = new TestApiFactory();
        var client = f.CreateClient();
        var token = await AuthFlowTests.LoginDemoAsync(client);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        var get = await client.GetAsync("/me/preferences/");
        Assert.Equal(HttpStatusCode.OK, get.StatusCode);
        var before = await get.Content.ReadFromJsonAsync<PrefDto>();

        var put = await client.PutAsJsonAsync("/me/preferences/", new
        {
            fontScale = 2.0f,
            highContrast = true,
            darkMode = (bool?)null,
            reducedMotion = (bool?)null,
            largeTargets = (bool?)null,
            plainLanguage = (bool?)null
        });
        Assert.Equal(HttpStatusCode.OK, put.StatusCode);
        var after = await put.Content.ReadFromJsonAsync<PrefDto>();
        Assert.Equal(2.0f, after!.fontScale);
        Assert.True(after.highContrast);
        // UpdatedAt debe refrescarse al FakeNow (mata mutante UpdatedAt)
        Assert.Equal(f.FakeTime.GetUtcNow().UtcDateTime, after.updatedAt);
    }

    private sealed record PrefDto(int idPreference, float fontScale, bool highContrast, bool darkMode,
        bool reducedMotion, bool largeTargets, bool plainLanguage, DateTime updatedAt);
}

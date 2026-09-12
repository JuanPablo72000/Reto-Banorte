using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.Extensions.Configuration;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes: quitar ConvertTimeFromUtc, quitar fallback, leer mal la key Business:TimeZoneId.
/// </summary>
public class BusinessClockTests
{
    private static IConfiguration Cfg(string? tz) =>
        new ConfigurationBuilder().AddInMemoryCollection(new Dictionary<string, string?>
        {
            ["Business:TimeZoneId"] = tz
        }).Build();

    [Fact]
    public void GetBusinessToday_ConvierteUtc_AZonaNegocio()
    {
        using var t = new TestDb();
        var clock = new BusinessClock(t.Time, Cfg("America/Mexico_City"));
        var utcNow = TestDb.FixedNow.UtcDateTime;
        DateOnly expected;
        try
        {
            var tz = TimeZoneInfo.FindSystemTimeZoneById("America/Mexico_City");
            expected = DateOnly.FromDateTime(TimeZoneInfo.ConvertTimeFromUtc(utcNow, tz));
        }
        catch { expected = DateOnly.FromDateTime(utcNow.Date); }
        Assert.Equal(expected, clock.GetBusinessToday());
    }

    [Fact]
    public void GetBusinessToday_TimeZoneInvalida_HaceFallbackAUtc()
    {
        using var t = new TestDb();
        var clock = new BusinessClock(t.Time, Cfg("Zona/No_Existe"));
        Assert.Equal(DateOnly.FromDateTime(TestDb.FixedNow.UtcDateTime.Date), clock.GetBusinessToday());
    }

    [Fact]
    public void GetBusinessToday_SinConfig_UltimoFallback()
    {
        using var t = new TestDb();
        var clock = new BusinessClock(t.Time, Cfg(null));
        var utcNow = TestDb.FixedNow.UtcDateTime;
        DateOnly expected;
        try
        {
            var tz = TimeZoneInfo.FindSystemTimeZoneById("America/Mexico_City");
            expected = DateOnly.FromDateTime(TimeZoneInfo.ConvertTimeFromUtc(utcNow, tz));
        }
        catch { expected = DateOnly.FromDateTime(utcNow.Date); }
        Assert.Equal(expected, clock.GetBusinessToday());
    }
}

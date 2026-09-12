using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Time.Testing;

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

    // Instante donde UTC y America/Mexico_City caen en días distintos:
    // 2026-06-16 00:30 UTC == 2026-06-15 18:30 en CDMX (UTC-6).
    // Cada mutante de la key/default colapsa la distinción y falla un test.
    private static readonly DateTimeOffset Frontera =
        new(2026, 6, 16, 0, 30, 0, TimeSpan.Zero);

    [Fact] // mata #847 (?? default) y #848 (key -> "")
    public void GetBusinessToday_TzExplicitaUtc_RespetaConfig()
    {
        var time = new FakeTimeProvider(Frontera);
        var clock = new BusinessClock(time, Cfg("UTC"));
        Assert.Equal(new DateOnly(2026, 6, 16), clock.GetBusinessToday());
    }

    [Fact] // mata #849 (default -> "")
    public void GetBusinessToday_SinConfig_ConvierteACdmx()
    {
        var time = new FakeTimeProvider(Frontera);
        var clock = new BusinessClock(time, Cfg(null));
        DateOnly expected;
        try
        {
            var tz = TimeZoneInfo.FindSystemTimeZoneById("America/Mexico_City");
            expected = DateOnly.FromDateTime(TimeZoneInfo.ConvertTimeFromUtc(
                Frontera.UtcDateTime, tz));
        }
        catch { expected = new DateOnly(2026, 6, 16); }
        Assert.Equal(expected, clock.GetBusinessToday());
        // En plataformas con la TZ disponible, el día negocio es el 15:
        try
        {
            TimeZoneInfo.FindSystemTimeZoneById("America/Mexico_City");
            Assert.Equal(new DateOnly(2026, 6, 15), clock.GetBusinessToday());
        }
        catch (TimeZoneNotFoundException) { /* fallback UTC: día 16, ya verificado */ }
    }
}

namespace BancaAdaptativa.Api.Services;

public interface IBusinessClock
{
    DateOnly GetBusinessToday();
}

public class BusinessClock(TimeProvider timeProvider, IConfiguration config) : IBusinessClock
{
    public DateOnly GetBusinessToday()
    {
        var tzId = config["Business:TimeZoneId"] ?? "America/Mexico_City";
        var utcNow = timeProvider.GetUtcNow().UtcDateTime;
        try
        {
            var tz = TimeZoneInfo.FindSystemTimeZoneById(tzId);
            return DateOnly.FromDateTime(TimeZoneInfo.ConvertTimeFromUtc(utcNow, tz));
        }
        catch
        {
            return DateOnly.FromDateTime(utcNow.Date);
        }
    }
}

namespace BancaAdaptativa.Api.Dtos.Common;

public record PagedResult<T>(IReadOnlyList<T> Items, int Total, int Limit, int Offset);

public record ServerTimeResponse(DateTime ServerTimeUtc, long UnixMilliseconds);

public record HealthResponse(string Status, DateTime ServerTimeUtc, string DbPath);

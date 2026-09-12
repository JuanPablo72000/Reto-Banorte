using BancaAdaptativa.Api.Data;
using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Time.Testing;

namespace BancaAdaptativa.Api.Tests.Helpers;

/// <summary>
/// Fábrica de DbContext aislado por test: SQLite in-memory + FakeTimeProvider congelado en UTC.
/// Mata mutantes de DateTime.Now/Today: todo instante sale del FakeTimeProvider.
/// </summary>
public sealed class TestDb : IDisposable
{
    private readonly SqliteConnection _conn;
    public AppDbContext Db { get; }
    public FakeTimeProvider Time { get; }

    public static readonly DateTimeOffset FixedNow =
        DateTimeOffset.UtcNow;

    public TestDb()
    {
        _conn = new SqliteConnection("DataSource=:memory:");
        _conn.Open();
        Time = new FakeTimeProvider(FixedNow);
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseSqlite(_conn)
            .Options;
        Db = new AppDbContext(options);
        Db.Database.EnsureCreated();
    }

    public void Dispose()
    {
        Db.Dispose();
        _conn.Dispose();
    }
}

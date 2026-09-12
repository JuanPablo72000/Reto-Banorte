using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using BancaAdaptativa.Api.Dtos.Preferences;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes: quitar asignación UpdatedAt, quitar ifs de campos opcionales, quitar throw PREFERENCES_NOT_FOUND.
/// </summary>
public class PreferenceServiceTests
{
    private static async Task<TestDb> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "P", Email = "p@p.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        t.Db.AccessibilityPreferences.Add(new AccessibilityPreference { IdUser = u.IdUser, UpdatedAt = now });
        await t.Db.SaveChangesAsync();
        return t;
    }

    [Fact]
    public async Task Update_ActualizaSoloCamposProvistos_YRefrescaUpdatedAt()
    {
        using var t = await ArrangeAsync();
        var uid = t.Db.Users.Select(u => u.IdUser).Single();
        var svc = new PreferenceService(t.Db, t.Time);

        var r = await svc.UpdateAsync(uid, new UpdatePreferencesRequest(2.0f, true, null, null, null, null));

        Assert.Equal(2.0f, r.FontScale);
        Assert.True(r.HighContrast);
        Assert.False(r.DarkMode); // no tocado
        Assert.Equal(TestDb.FixedNow.UtcDateTime, r.UpdatedAt); // mata: quitar UpdatedAt =
        Assert.Equal(DateTimeKind.Utc, r.UpdatedAt.Kind);
    }

    [Fact]
    public async Task Get_NotFound_Lanza()
    {
        using var t = new TestDb();
        var svc = new PreferenceService(t.Db, t.Time);
        await Assert.ThrowsAsync<KeyNotFoundException>(() => svc.GetAsync(999));
    }

    [Fact]
    public async Task Update_NotFound_Lanza()
    {
        using var t = new TestDb();
        var svc = new PreferenceService(t.Db, t.Time);
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.UpdateAsync(999, new UpdatePreferencesRequest(null, true, null, null, null, null)));
    }
}

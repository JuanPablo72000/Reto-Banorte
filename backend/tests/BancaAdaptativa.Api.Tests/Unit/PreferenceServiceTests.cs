using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;
using BancaAdaptativa.Api.Dtos.Preferences;
using Microsoft.EntityFrameworkCore;

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
        // Semilla con instante ANTERIOR al FakeNow: si el SUT no refresca UpdatedAt,
        // el valor viejo delata al mutante #864.
        t.Db.AccessibilityPreferences.Add(new AccessibilityPreference
            { IdUser = u.IdUser, UpdatedAt = now.AddHours(-5) });
        await t.Db.SaveChangesAsync();
        t.Db.ChangeTracker.Clear();
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

        // Persistencia real (no solo objeto trackeado): mata #864 aunque devuelva el DTO.
        t.Db.ChangeTracker.Clear();
        var persisted = await t.Db.AccessibilityPreferences.AsNoTracking()
            .SingleAsync(p => p.IdUser == uid);
        Assert.Equal(TestDb.FixedNow.UtcDateTime, persisted.UpdatedAt);
        Assert.Equal(2.0f, persisted.FontScale);
    }

    [Fact]
    public async Task Get_NotFound_MensajePreferencesNotFound()
    {
        using var t = new TestDb();
        var svc = new PreferenceService(t.Db, t.Time);
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() => svc.GetAsync(999));
        Assert.Equal("PREFERENCES_NOT_FOUND", ex.Message); // mata #854
    }

    [Fact]
    public async Task Update_NotFound_MensajePreferencesNotFound()
    {
        using var t = new TestDb();
        var svc = new PreferenceService(t.Db, t.Time);
        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.UpdateAsync(999, new UpdatePreferencesRequest(null, true, null, null, null, null)));
        Assert.Equal("PREFERENCES_NOT_FOUND", ex.Message); // mata #857
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

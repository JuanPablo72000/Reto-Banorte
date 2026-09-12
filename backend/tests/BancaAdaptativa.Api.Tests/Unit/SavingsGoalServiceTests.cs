using BancaAdaptativa.Api.Dtos.SavingsGoals;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Unit;

public class SavingsGoalServiceTests
{
    private static async Task<(TestDb t, int uid)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var u = new User { Name = "G", Email = "g@g.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(u);
        await t.Db.SaveChangesAsync();
        return (t, u.IdUser);
    }

    [Fact]
    public async Task Create_Contribute_CompletaAlLlegarALaMeta()
    {
        var (t, uid) = await ArrangeAsync();
        using var _ = t;
        var svc = new SavingsGoalService(t.Db, t.Time);

        var created = await svc.CreateAsync(uid, new CreateSavingsGoalRequest("Viaje", 10000m, TestDb.FixedNow.UtcDateTime.AddMonths(3)));
        Assert.Equal(0m, created.CurrentAmount);
        Assert.Equal(0m, created.ProgressPercent);
        Assert.Equal("active", created.Status);

        var half = await svc.ContributeAsync(uid, created.IdGoal, 4000m);
        Assert.Equal(4000m, half.CurrentAmount);
        Assert.Equal(40m, half.ProgressPercent);
        Assert.Equal("active", half.Status);

        var done = await svc.ContributeAsync(uid, created.IdGoal, 6000m);
        Assert.Equal("completed", done.Status);
        Assert.Equal(100m, done.ProgressPercent);
    }

    [Fact]
    public async Task Contribute_MetaPausada_LanzaGoalNotActive()
    {
        var (t, uid) = await ArrangeAsync();
        using var _ = t;
        var svc = new SavingsGoalService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, new CreateSavingsGoalRequest("X", 100m, TestDb.FixedNow.UtcDateTime));
        await svc.SetStatusAsync(uid, created.IdGoal, "paused");

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            svc.ContributeAsync(uid, created.IdGoal, 10m));
        Assert.Equal("GOAL_NOT_ACTIVE", ex.Message);
    }

    [Fact]
    public async Task SetStatus_EstadoInvalido_Lanza()
    {
        var (t, uid) = await ArrangeAsync();
        using var _ = t;
        var svc = new SavingsGoalService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, new CreateSavingsGoalRequest("X", 100m, TestDb.FixedNow.UtcDateTime));
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            svc.SetStatusAsync(uid, created.IdGoal, "zzz"));
    }

    [Fact]
    public async Task Contribute_MontoNoPositivo_Lanza()
    {
        var (t, uid) = await ArrangeAsync();
        using var _ = t;
        var svc = new SavingsGoalService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, new CreateSavingsGoalRequest("X", 100m, TestDb.FixedNow.UtcDateTime));
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() =>
            svc.ContributeAsync(uid, created.IdGoal, 0m));
    }
}

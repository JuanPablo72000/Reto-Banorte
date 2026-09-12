using BancaAdaptativa.Api.Data;
using BancaAdaptativa.Api.Dtos.Transfers;
using BancaAdaptativa.Api.Models;
using BancaAdaptativa.Api.Services;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Unit;

/// <summary>
/// Mutantes que estos tests deben matar (Stryker):
/// - quitar early-return idempotente (if existing is not null)
/// - quitar Trim()/ToUpperInvariant() en Currency/Destination
/// - cambiar Status "pending"/"confirmed" o quitar ConfirmedAt
/// - cambiar umbral RiskLevel (> 10000) o quitar AuditLog/Confirmation
/// - cambiar != "pending" por == en Confirm
/// </summary>
public class TransferServiceTests
{
    private static async Task<(TestDb t, int userId, int accountId)> ArrangeAsync()
    {
        var t = new TestDb();
        var now = TestDb.FixedNow.UtcDateTime;
        var user = new User { Name = "T", Email = "t@t.mx", PasswordHash = "x", CreatedAt = now };
        t.Db.Users.Add(user);
        await t.Db.SaveChangesAsync();
        var acc = new Account
        {
            IdUser = user.IdUser, AccountType = "debito", Alias = "A",
            MaskedNumber = "****1", Currency = "MXN", Balance = 50000m,
            Status = "active", CreatedAt = now
        };
        t.Db.Accounts.Add(acc);
        await t.Db.SaveChangesAsync();
        return (t, user.IdUser, acc.IdAccount);
    }

    private static CreateTransferRequest Req(int accountId, string? key = "k-1") =>
        new(accountId, "Mamá", "****5678", 2000m, "mxn", "Apoyo", key);

    [Fact]
    public async Task Create_AsignaPending_SinConfirmedAt_YNormalizaCurrency()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var r = await svc.CreateAsync(uid, Req(acc));

        Assert.Equal("pending", r.Status);
        Assert.Null(r.ConfirmedAt);
        Assert.Equal("MXN", r.Currency); // mata mutante: quitar ToUpperInvariant
        Assert.Equal("k-1", r.IdempotencyKey);
    }

    [Fact]
    public async Task Create_GeneraKey_CuandoVacia()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var r = await svc.CreateAsync(uid, Req(acc, null));

        Assert.False(string.IsNullOrWhiteSpace(r.IdempotencyKey)); // mata: Guid.NewGuid eliminado
    }

    [Fact]
    public async Task Create_EsIdempotente_MismaKeyDevuelveMismoTransfer()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var a = await svc.CreateAsync(uid, Req(acc, "dup-key"));
        var b = await svc.CreateAsync(uid, Req(acc, "dup-key"));

        Assert.Equal(a.IdTransfer, b.IdTransfer); // mata: quitar early-return existing
        Assert.Equal(1, t.Db.Transfers.Count(x => x.IdempotencyKey == "dup-key"));
    }

    [Fact]
    public async Task Create_RechazaCuentaDeOtroUsuario()
    {
        var (t, uid, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new TransferService(t.Db, t.Time);

        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.CreateAsync(uid, Req(9999, "otra"))); // mata: quitar validación owns
    }

    [Fact]
    public async Task Confirm_CambiaAConfirmed_CreaConfirmationYAuditLog()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "c-1"));

        var (tr, conf) = await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        Assert.Equal("confirmed", tr.Status); // mata: Status no cambia / cambia a otro valor
        Assert.Equal(TestDb.FixedNow.UtcDateTime, tr.ConfirmedAt); // mata: quitar asignación ConfirmedAt
        Assert.Equal("confirmed", conf.Status);
        Assert.Equal(TestDb.FixedNow.UtcDateTime, conf.ConfirmedAt);
        var audit = t.Db.AuditLogs.Single(a => a.Resource == $"transfer:{tr.IdTransfer}");
        Assert.Equal("low", audit.RiskLevel); // 2000 <= 10000
        Assert.Equal(TestDb.FixedNow.UtcDateTime, audit.CreatedAt);
    }

    [Fact]
    public async Task Confirm_MarcaRiskMedium_CuandoMontoMayorA10000()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 15000m, "MXN", "", "big-1"));

        var (tr, _) = await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        Assert.Equal("medium", t.Db.AuditLogs.Single(a => a.Resource == $"transfer:{tr.IdTransfer}").RiskLevel);
        // mata mutantes: > por >=, 10000 por otro valor, medium por low
    }

    [Fact]
    public async Task Confirm_DobleConfirm_LanzaTransferNotPending()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "d-1"));
        await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        await Assert.ThrowsAsync<InvalidOperationException>(() =>
            svc.ConfirmAsync(uid, created.IdTransfer, "app")); // mata: != cambiado a == o validación eliminada
    }

    [Fact]
    public async Task Confirm_MethodVacio_UsaDefaultApp()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "m-1"));

        var (_, conf) = await svc.ConfirmAsync(uid, created.IdTransfer, "  ");

        Assert.Equal("app", conf.Method); // mata: quitar default IsNullOrWhiteSpace
    }

    [Fact] // mata #923: t.IdempotencyKey != key
    public async Task Create_KeysDistintas_CreanTransfersDistintos()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var a = await svc.CreateAsync(uid, Req(acc, "key-A"));
        var b = await svc.CreateAsync(uid, Req(acc, "key-B"));

        Assert.NotEqual(a.IdTransfer, b.IdTransfer);
    }

    [Fact] // mata #930: ORIGIN_ACCOUNT_NOT_FOUND -> ""
    public async Task Create_CuentaAjena_MensajeOriginAccountNotFound()
    {
        var (t, uid, _) = await ArrangeAsync();
        using var _2 = t;
        var svc = new TransferService(t.Db, t.Time);

        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.CreateAsync(uid, Req(9999, "otra")));
        Assert.Equal("ORIGIN_ACCOUNT_NOT_FOUND", ex.Message);
    }

    [Fact] // mata #932/#934-936 y #937: currency en blanco -> MXN
    public async Task Create_CurrencyVacia_UsaDefaultMXN()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var r = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 100m, "   ", "C", "cur-blank"));

        Assert.Equal("MXN", r.Currency);
    }

    [Fact] // mata #932/#933: true->MXN / false->ToUpper pierden el valor real
    public async Task Create_CurrencyUsd_NormalizaAUSD()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var r = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 100m, "usd", "C", "cur-usd"));

        Assert.Equal("USD", r.Currency);
    }

    [Fact] // mata #938 (?? string.Empty) y #939 (string.Empty -> basura)
    public async Task Create_Concept_PersisteValorYNuloVaAVacio()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);

        var conTexto = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 100m, "MXN", "Apoyo quincena", "conc-1"));
        Assert.Equal("Apoyo quincena", conTexto.Concept);

        var conNulo = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 100m, "MXN", null!, "conc-2"));
        Assert.Equal(string.Empty, conNulo.Concept);
    }

    [Fact] // mata #946-949 y #950: GetAsync sin cobertura
    public async Task Get_Ok_AjenoYMisingLanzanTransferNotFound()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "g-1"));

        var got = await svc.GetAsync(uid, created.IdTransfer);
        Assert.Equal(created.IdTransfer, got.IdTransfer);

        var exAjeno = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.GetAsync(9999, created.IdTransfer));
        Assert.Equal("TRANSFER_NOT_FOUND", exAjeno.Message);

        var exMissing = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.GetAsync(uid, 999999));
        Assert.Equal("TRANSFER_NOT_FOUND", exMissing.Message);
    }

    [Fact] // mata #952 (|| en lookup de Confirm) y #955 (mensaje)
    public async Task Confirm_UsuarioAjeno_LanzaTransferNotFound()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "aj-1"));

        var ex = await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            svc.ConfirmAsync(9999, created.IdTransfer, "app"));
        Assert.Equal("TRANSFER_NOT_FOUND", ex.Message);
    }

    [Fact] // mata #959: TRANSFER_NOT_PENDING -> ""
    public async Task Confirm_DobleConfirm_MensajeTransferNotPending()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "d-2"));
        await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            svc.ConfirmAsync(uid, created.IdTransfer, "app"));
        Assert.Equal("TRANSFER_NOT_PENDING", ex.Message);
    }

    [Fact] // mata #977: >= 10000 (frontera exacta -> low)
    public async Task Confirm_MontoExacto10000_EsLow()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, new CreateTransferRequest(
            acc, "D", "****9", 10000m, "MXN", "", "edge-10k"));

        var (tr, _) = await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        Assert.Equal("low", t.Db.AuditLogs.Single(a => a.Resource == $"transfer:{tr.IdTransfer}").RiskLevel);
    }

    [Fact] // mata #980: RedactedPayload -> $""
    public async Task Confirm_AuditLog_ContienePayloadRedactado()
    {
        var (t, uid, acc) = await ArrangeAsync();
        using var _ = t;
        var svc = new TransferService(t.Db, t.Time);
        var created = await svc.CreateAsync(uid, Req(acc, "pl-1"));

        var (tr, _) = await svc.ConfirmAsync(uid, created.IdTransfer, "app");

        var payload = t.Db.AuditLogs.Single(a => a.Resource == $"transfer:{tr.IdTransfer}").RedactedPayload;
        Assert.Contains("****5678", payload);
        Assert.Contains("2000", payload);
    }
}

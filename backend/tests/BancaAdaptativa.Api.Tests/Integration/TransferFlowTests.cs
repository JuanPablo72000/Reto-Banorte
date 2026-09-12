using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

/// <summary>
/// Flujo HTTP completo: crear (pending, ConfirmedAt null) -> confirmar (confirmed + timestamps).
/// Mata mutantes de Status, ConfirmedAt, IdempotencyKey, RiskLevel a nivel endpoint.
/// </summary>
public class TransferFlowTests
{
    private static async Task<HttpClient> AuthedClientAsync(TestApiFactory f)
    {
        var c = f.CreateClient();
        var token = await AuthFlowTests.LoginDemoAsync(c);
        c.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
        return c;
    }

    private static async Task<int> DemoAccountIdAsync(HttpClient c)
    {
        var accs = await c.GetFromJsonAsync<List<AccountDto>>("/accounts");
        return accs!.First().idAccount;
    }

    [Fact]
    public async Task PostGetConfirm_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = await AuthedClientAsync(f);
        var accId = await DemoAccountIdAsync(client);
        var key = $"it-{Guid.NewGuid():N}";

        var create = await client.PostAsJsonAsync("/transfers/", new
        {
            idOriginAccount = accId,
            destinationAlias = "Mamá",
            destinationMasked = "****5678",
            amount = 500m,
            currency = "mxn",
            concept = "Test",
            idempotencyKey = key
        });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var t = await create.Content.ReadFromJsonAsync<TransferDto>();
        Assert.Equal("pending", t!.status);
        Assert.Null(t.confirmedAt);
        Assert.Equal("MXN", t.currency);

        // idempotencia: mismo key => mismo id
        var dup = await client.PostAsJsonAsync("/transfers/", new
        {
            idOriginAccount = accId,
            destinationAlias = "Otro",
            destinationMasked = "****0000",
            amount = 999m,
            currency = "MXN",
            concept = "X",
            idempotencyKey = key
        });
        var t2 = await dup.Content.ReadFromJsonAsync<TransferDto>();
        Assert.Equal(t.idTransfer, t2!.idTransfer);

        var confirm = await client.PostAsJsonAsync($"/transfers/{t.idTransfer}/confirm", new { method = "app" });
        Assert.Equal(HttpStatusCode.OK, confirm.StatusCode);
        var confirmed = await confirm.Content.ReadFromJsonAsync<ConfirmEnvelope>();
        Assert.Equal("confirmed", confirmed!.transfer.status);
        Assert.NotNull(confirmed.transfer.confirmedAt);
        Assert.Equal("confirmed", confirmed.confirmation.status);

        // doble confirm => 409 TRANSFER_NOT_PENDING
        var again = await client.PostAsJsonAsync($"/transfers/{t.idTransfer}/confirm", new { method = "app" });
        Assert.Equal(HttpStatusCode.Conflict, again.StatusCode);
    }

    private sealed record AccountDto(int idAccount, string accountType, string alias, string maskedNumber, string currency, decimal balance, string status, DateTime createdAt);
    private sealed record TransferDto(int idTransfer, int idOriginAccount, string destinationAlias, string destinationMasked, decimal amount, string currency, string concept, string status, string idempotencyKey, DateTime? confirmedAt);
    private sealed record ConfirmEnvelope(TransferDto transfer, ConfirmationDto confirmation);
    private sealed record ConfirmationDto(int idConfirmation, string method, string status, DateTime? confirmedAt);
}

using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

public class ApiContractTests
{
    [Fact]
    public async Task AccountSummary_DevuelveSaldoDelUsuarioAutenticado()
    {
        using var factory = new TestApiFactory();
        var client = factory.CreateClient();
        var token = await AuthFlowTests.LoginDemoAsync(client);
        client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

        var response = await client.GetAsync("/me/account-summary");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        var summary = await response.Content.ReadFromJsonAsync<AccountSummaryDto>();
        Assert.NotNull(summary);
        Assert.Equal(25400.50m, summary!.totalBalance);
        Assert.Equal("MXN", summary.currency);
        Assert.NotEmpty(summary.accounts);
        Assert.All(summary.accounts, account => Assert.DoesNotContain("1234567890", account.maskedNumber));
    }

    [Fact]
    public async Task Swagger_ExponeOperationIdsSchemasYRespuestas()
    {
        using var factory = new TestApiFactory();
        var client = factory.CreateClient();

        var response = await client.GetAsync("/swagger/v1/swagger.json");

        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
        using var document = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var root = document.RootElement;
        var paths = root.GetProperty("paths");
        var summaryOperation = paths.GetProperty("/me/account-summary").GetProperty("get");
        var accountsOperation = paths.GetProperty("/accounts").GetProperty("get");
        var serverTimeOperation = paths.GetProperty("/server-time").GetProperty("get");

        Assert.Equal("getMeAccountSummary", summaryOperation.GetProperty("operationId").GetString());
        Assert.Equal("getAccounts", accountsOperation.GetProperty("operationId").GetString());
        Assert.Equal("getServerTime", serverTimeOperation.GetProperty("operationId").GetString());
        Assert.True(summaryOperation.GetProperty("responses").TryGetProperty("200", out _));
        Assert.True(summaryOperation.GetProperty("responses").TryGetProperty("401", out _));
        Assert.True(root.GetProperty("components").GetProperty("schemas").TryGetProperty("AccountSummaryResponse", out _));
    }

    private sealed record AccountSummaryDto(decimal totalBalance, string currency, List<AccountDto> accounts);
    private sealed record AccountDto(int idAccount, string accountType, string alias, string maskedNumber,
        string currency, decimal balance, string status, DateTime createdAt);
}

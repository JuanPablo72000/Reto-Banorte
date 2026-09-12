using System.Net;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using BancaAdaptativa.Api.Tests.Helpers;

namespace BancaAdaptativa.Api.Tests.Integration;

public class PersonalFinanceFlowTests
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
    public async Task Statements_GenerateListDetail_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = await AuthedClientAsync(f);
        var accId = await DemoAccountIdAsync(client);

        var gen = await client.PostAsync(
            $"/accounts/{accId}/statements/generate?year=2026&month=6&cutOffDay=15", null);
        Assert.Equal(HttpStatusCode.Created, gen.StatusCode);
        var stmt = await gen.Content.ReadFromJsonAsync<StatementDto>();
        Assert.Equal(new DateOnly(2026, 5, 16), stmt!.periodStart);
        Assert.Equal(new DateOnly(2026, 6, 15), stmt.periodEnd);

        var list = await client.GetFromJsonAsync<List<StatementDto>>(
            $"/accounts/{accId}/statements?year=2026&month=6");
        Assert.Single(list!);

        var detail = await client.GetFromJsonAsync<StatementDetailDto>(
            $"/accounts/{accId}/statements/{stmt.idStatement}");
        Assert.Equal(stmt.idStatement, detail!.statement.idStatement);
        Assert.NotNull(detail.expenses);

        var cats = await client.GetFromJsonAsync<List<CategoryDto>>("/expense-categories");
        Assert.True(cats!.Count >= 10);

        // cuenta ajena => 404
        var other = await client.GetAsync("/accounts/999999/statements");
        Assert.Equal(HttpStatusCode.NotFound, other.StatusCode);
    }

    [Fact]
    public async Task Budgets_CreateMonthly_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = await AuthedClientAsync(f);

        var cats = await client.GetFromJsonAsync<List<CategoryDto>>("/expense-categories");
        var super = cats!.Single(c => c.code == "supermarket");

        var create = await client.PostAsJsonAsync("/me/budgets/", new
        {
            idExpenseCategory = super.idCategory,
            month = 6,
            year = 2026,
            amountLimit = 5000m
        });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);

        var summary = await client.GetFromJsonAsync<BudgetSummaryDto>(
            "/me/budgets/monthly?year=2026&month=6");
        Assert.Equal(6, summary!.month);
        Assert.Single(summary.budgets);

        var bad = await client.PostAsJsonAsync("/me/budgets/", new
        {
            idExpenseCategory = 999999,
            month = 6,
            year = 2026,
            amountLimit = 100m
        });
        Assert.Equal(HttpStatusCode.BadRequest, bad.StatusCode);
    }

    [Fact]
    public async Task SavingsGoals_CreateContribute_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = await AuthedClientAsync(f);

        var create = await client.PostAsJsonAsync("/me/savings-goals/", new
        {
            name = "Viaje",
            targetAmount = 10000m,
            targetDate = DateTime.UtcNow.AddMonths(3)
        });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var goal = await create.Content.ReadFromJsonAsync<GoalDto>();

        var contribute = await client.PostAsJsonAsync(
            $"/me/savings-goals/{goal!.idGoal}/contribute", new { amount = 4000m });
        Assert.Equal(HttpStatusCode.OK, contribute.StatusCode);
        var updated = await contribute.Content.ReadFromJsonAsync<GoalDto>();
        Assert.Equal(4000m, updated!.currentAmount);

        var list = await client.GetFromJsonAsync<List<GoalDto>>("/me/savings-goals/");
        Assert.Contains(list!, g => g.idGoal == goal.idGoal);
    }

    [Fact]
    public async Task CreditCards_CreateStatementPay_FlujoCompleto()
    {
        using var f = new TestApiFactory();
        var client = await AuthedClientAsync(f);

        var create = await client.PostAsJsonAsync("/me/credit-cards", new
        {
            cardNumberMasked = "****9999",
            cardType = "Mastercard",
            creditLimit = 20000m,
            interestRate = 30m,
            statementCutOffDay = 15,
            paymentDueDay = 5
        });
        Assert.Equal(HttpStatusCode.Created, create.StatusCode);
        var card = await create.Content.ReadFromJsonAsync<CardDto>();
        Assert.Equal(20000m, card!.availableCredit);

        var gen = await client.PostAsync(
            $"/me/credit-cards/{card.idCreditCard}/statements/generate?year=2026&month=6&totalPurchases=2000&totalPayments=500", null);
        Assert.Equal(HttpStatusCode.Created, gen.StatusCode);
        var stmt = await gen.Content.ReadFromJsonAsync<CardStatementDto>();
        Assert.Equal(0m, stmt!.interestCharges);
        Assert.Equal(75m, stmt.minimumPayment); // 5% de 1500

        var pay = await client.PostAsJsonAsync(
            $"/me/credit-cards/{card.idCreditCard}/pay", new { amount = 500m });
        Assert.Equal(HttpStatusCode.OK, pay.StatusCode);
        var paid = await pay.Content.ReadFromJsonAsync<CardDto>();
        Assert.Equal(19000m, paid!.availableCredit);

        var list = await client.GetFromJsonAsync<List<CardStatementDto>>(
            $"/me/credit-cards/{card.idCreditCard}/statements");
        Assert.Single(list!);
    }

    private sealed record AccountDto(int idAccount, string accountType, string alias, string maskedNumber, string currency, decimal balance, string status, DateTime createdAt);
    private sealed record StatementDto(int idStatement, int idAccount, int cutOffDay, DateOnly periodStart, DateOnly periodEnd, decimal openingBalance, decimal closingBalance, decimal totalCredits, decimal totalDebits, int transactionCount, string accountType, string status, DateTime generatedAt);
    private sealed record ExpenseBreakdownDto(int idExpenseCategory, string categoryName, string categoryCode, decimal amount, int transactionCount, DateOnly? firstTransactionDate, DateOnly? lastTransactionDate);
    private sealed record StatementDetailDto(StatementDto statement, List<ExpenseBreakdownDto> expenses);
    private sealed record CategoryDto(int idCategory, string name, string code, string icon, bool isDefault, int sortOrder);
    private sealed record BudgetDto(int idBudget, int idExpenseCategory, string categoryName, string categoryCode, int month, int year, decimal amountLimit, decimal currentSpent, decimal usagePercent, string status);
    private sealed record BudgetSummaryDto(int month, int year, decimal totalLimit, decimal totalSpent, List<BudgetDto> budgets);
    private sealed record GoalDto(int idGoal, string name, decimal targetAmount, decimal currentAmount, decimal progressPercent, DateTime targetDate, string status, DateTime createdAt, DateTime updatedAt);
    private sealed record CardDto(int idCreditCard, string cardNumberMasked, string cardType, decimal creditLimit, decimal availableCredit, decimal interestRate, int statementCutOffDay, int paymentDueDay, string status, DateTime createdAt);
    private sealed record CardStatementDto(int idCreditCardStatement, int idCreditCard, int idStatement, DateOnly periodStart, DateOnly periodEnd, decimal previousBalance, decimal totalPayments, decimal totalCredits, decimal totalPurchases, decimal interestCharges, decimal minimumPayment, DateOnly paymentDueDate, decimal availableCredit, string status, DateTime generatedAt);
}

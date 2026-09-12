using System.ComponentModel.DataAnnotations;

namespace BancaAdaptativa.Api.Dtos.Accounts;

public record CreateCreditCardRequest(
    [Required, MaxLength(20)] string CardNumberMasked,
    [MaxLength(20)] string CardType,
    [Range(1, 10000000)] decimal CreditLimit,
    [Range(0, 100)] decimal InterestRate,
    [Range(1, 31)] int StatementCutOffDay,
    [Range(1, 31)] int PaymentDueDay);

public record CreditCardResponse(
    int IdCreditCard, string CardNumberMasked, string CardType,
    decimal CreditLimit, decimal AvailableCredit, decimal InterestRate,
    int StatementCutOffDay, int PaymentDueDay, string Status, DateTime CreatedAt);

public record CreditCardStatementResponse(
    int IdCreditCardStatement, int IdCreditCard, int IdStatement,
    DateOnly PeriodStart, DateOnly PeriodEnd,
    decimal PreviousBalance, decimal TotalPayments, decimal TotalCredits,
    decimal TotalPurchases, decimal InterestCharges, decimal MinimumPayment,
    DateOnly PaymentDueDate, decimal AvailableCredit,
    string Status, DateTime GeneratedAt);

public record PayCreditCardRequest(
    [Range(0.01, 10000000)] decimal Amount);

using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace BancaAdaptativa.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class StatementsBudgetsGoalsCards : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<int>(
                name: "IdExpenseCategory",
                table: "Transactions",
                type: "INTEGER",
                nullable: true);

            migrationBuilder.CreateTable(
                name: "CreditCards",
                columns: table => new
                {
                    IdCreditCard = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdUser = table.Column<int>(type: "INTEGER", nullable: false),
                    CardNumberMasked = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    CardType = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    CreditLimit = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    AvailableCredit = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    InterestRate = table.Column<decimal>(type: "TEXT", nullable: false),
                    StatementCutOffDay = table.Column<int>(type: "INTEGER", nullable: false),
                    PaymentDueDay = table.Column<int>(type: "INTEGER", nullable: false),
                    Status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CreditCards", x => x.IdCreditCard);
                    table.ForeignKey(
                        name: "FK_CreditCards_Users_IdUser",
                        column: x => x.IdUser,
                        principalTable: "Users",
                        principalColumn: "IdUser",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "ExpenseCategories",
                columns: table => new
                {
                    IdCategory = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    Name = table.Column<string>(type: "TEXT", maxLength: 60, nullable: false),
                    Code = table.Column<string>(type: "TEXT", maxLength: 30, nullable: false),
                    Icon = table.Column<string>(type: "TEXT", maxLength: 40, nullable: false),
                    IsDefault = table.Column<bool>(type: "INTEGER", nullable: false),
                    SortOrder = table.Column<int>(type: "INTEGER", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_ExpenseCategories", x => x.IdCategory);
                });

            migrationBuilder.CreateTable(
                name: "SavingsGoals",
                columns: table => new
                {
                    IdGoal = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdUser = table.Column<int>(type: "INTEGER", nullable: false),
                    Name = table.Column<string>(type: "TEXT", maxLength: 100, nullable: false),
                    TargetAmount = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    CurrentAmount = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TargetDate = table.Column<DateTime>(type: "TEXT", nullable: false),
                    Status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_SavingsGoals", x => x.IdGoal);
                    table.ForeignKey(
                        name: "FK_SavingsGoals_Users_IdUser",
                        column: x => x.IdUser,
                        principalTable: "Users",
                        principalColumn: "IdUser",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Statements",
                columns: table => new
                {
                    IdStatement = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdAccount = table.Column<int>(type: "INTEGER", nullable: false),
                    CutOffDay = table.Column<int>(type: "INTEGER", nullable: false),
                    PeriodStart = table.Column<string>(type: "TEXT", nullable: false),
                    PeriodEnd = table.Column<string>(type: "TEXT", nullable: false),
                    OpeningBalance = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    ClosingBalance = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TotalCredits = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TotalDebits = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TransactionCount = table.Column<int>(type: "INTEGER", nullable: false),
                    AccountType = table.Column<string>(type: "TEXT", maxLength: 30, nullable: false),
                    Status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    GeneratedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Statements", x => x.IdStatement);
                    table.ForeignKey(
                        name: "FK_Statements_Accounts_IdAccount",
                        column: x => x.IdAccount,
                        principalTable: "Accounts",
                        principalColumn: "IdAccount",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Budgets",
                columns: table => new
                {
                    IdBudget = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdUser = table.Column<int>(type: "INTEGER", nullable: false),
                    IdExpenseCategory = table.Column<int>(type: "INTEGER", nullable: false),
                    Month = table.Column<int>(type: "INTEGER", nullable: false),
                    Year = table.Column<int>(type: "INTEGER", nullable: false),
                    AmountLimit = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    CurrentSpent = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    StartDate = table.Column<DateTime>(type: "TEXT", nullable: false),
                    EndDate = table.Column<DateTime>(type: "TEXT", nullable: false),
                    Status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "TEXT", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Budgets", x => x.IdBudget);
                    table.ForeignKey(
                        name: "FK_Budgets_ExpenseCategories_IdExpenseCategory",
                        column: x => x.IdExpenseCategory,
                        principalTable: "ExpenseCategories",
                        principalColumn: "IdCategory",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_Budgets_Users_IdUser",
                        column: x => x.IdUser,
                        principalTable: "Users",
                        principalColumn: "IdUser",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "CreditCardStatements",
                columns: table => new
                {
                    IdCreditCardStatement = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdCreditCard = table.Column<int>(type: "INTEGER", nullable: false),
                    IdStatement = table.Column<int>(type: "INTEGER", nullable: false),
                    PreviousBalance = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TotalPayments = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TotalCredits = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TotalPurchases = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    InterestCharges = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    MinimumPayment = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    PaymentDueDate = table.Column<string>(type: "TEXT", nullable: false),
                    AvailableCredit = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    Status = table.Column<string>(type: "TEXT", maxLength: 20, nullable: false),
                    GeneratedAt = table.Column<DateTime>(type: "TEXT", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CreditCardStatements", x => x.IdCreditCardStatement);
                    table.ForeignKey(
                        name: "FK_CreditCardStatements_CreditCards_IdCreditCard",
                        column: x => x.IdCreditCard,
                        principalTable: "CreditCards",
                        principalColumn: "IdCreditCard",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_CreditCardStatements_Statements_IdStatement",
                        column: x => x.IdStatement,
                        principalTable: "Statements",
                        principalColumn: "IdStatement",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "StatementExpenses",
                columns: table => new
                {
                    IdStatementExpense = table.Column<int>(type: "INTEGER", nullable: false)
                        .Annotation("Sqlite:Autoincrement", true),
                    IdStatement = table.Column<int>(type: "INTEGER", nullable: false),
                    IdExpenseCategory = table.Column<int>(type: "INTEGER", nullable: false),
                    Amount = table.Column<decimal>(type: "decimal(18,2)", nullable: false),
                    TransactionCount = table.Column<int>(type: "INTEGER", nullable: false),
                    FirstTransactionDate = table.Column<string>(type: "TEXT", nullable: true),
                    LastTransactionDate = table.Column<string>(type: "TEXT", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_StatementExpenses", x => x.IdStatementExpense);
                    table.ForeignKey(
                        name: "FK_StatementExpenses_ExpenseCategories_IdExpenseCategory",
                        column: x => x.IdExpenseCategory,
                        principalTable: "ExpenseCategories",
                        principalColumn: "IdCategory",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_StatementExpenses_Statements_IdStatement",
                        column: x => x.IdStatement,
                        principalTable: "Statements",
                        principalColumn: "IdStatement",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Transactions_IdExpenseCategory",
                table: "Transactions",
                column: "IdExpenseCategory");

            migrationBuilder.CreateIndex(
                name: "IX_Budgets_IdExpenseCategory",
                table: "Budgets",
                column: "IdExpenseCategory");

            migrationBuilder.CreateIndex(
                name: "IX_Budgets_IdUser_IdExpenseCategory_Month_Year",
                table: "Budgets",
                columns: new[] { "IdUser", "IdExpenseCategory", "Month", "Year" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_CreditCards_IdUser",
                table: "CreditCards",
                column: "IdUser");

            migrationBuilder.CreateIndex(
                name: "IX_CreditCardStatements_IdCreditCard",
                table: "CreditCardStatements",
                column: "IdCreditCard");

            migrationBuilder.CreateIndex(
                name: "IX_CreditCardStatements_IdStatement",
                table: "CreditCardStatements",
                column: "IdStatement",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_ExpenseCategories_Code",
                table: "ExpenseCategories",
                column: "Code",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_SavingsGoals_IdUser",
                table: "SavingsGoals",
                column: "IdUser");

            migrationBuilder.CreateIndex(
                name: "IX_StatementExpenses_IdExpenseCategory",
                table: "StatementExpenses",
                column: "IdExpenseCategory");

            migrationBuilder.CreateIndex(
                name: "IX_StatementExpenses_IdStatement_IdExpenseCategory",
                table: "StatementExpenses",
                columns: new[] { "IdStatement", "IdExpenseCategory" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Statements_IdAccount_PeriodStart",
                table: "Statements",
                columns: new[] { "IdAccount", "PeriodStart" },
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_Transactions_ExpenseCategories_IdExpenseCategory",
                table: "Transactions",
                column: "IdExpenseCategory",
                principalTable: "ExpenseCategories",
                principalColumn: "IdCategory",
                onDelete: ReferentialAction.SetNull);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Transactions_ExpenseCategories_IdExpenseCategory",
                table: "Transactions");

            migrationBuilder.DropTable(
                name: "Budgets");

            migrationBuilder.DropTable(
                name: "CreditCardStatements");

            migrationBuilder.DropTable(
                name: "SavingsGoals");

            migrationBuilder.DropTable(
                name: "StatementExpenses");

            migrationBuilder.DropTable(
                name: "CreditCards");

            migrationBuilder.DropTable(
                name: "ExpenseCategories");

            migrationBuilder.DropTable(
                name: "Statements");

            migrationBuilder.DropIndex(
                name: "IX_Transactions_IdExpenseCategory",
                table: "Transactions");

            migrationBuilder.DropColumn(
                name: "IdExpenseCategory",
                table: "Transactions");
        }
    }
}

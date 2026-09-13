// Cliente REST del backend .NET (BancaAdaptativa.Api).
// Llamadas directas desde el navegador: el backend ya permite CORS para
// localhost:3000 (Program.cs). NEXT_PUBLIC_API_URL se define en
// docker-compose (http://localhost:8000); en dev local el backend corre
// en 5178 (Properties/launchSettings.json).

export const API_URL =
    process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:5178";

const TIMEOUT_MS = 8000;

/** El backend no respondió (apagado / red): las páginas caen a datos demo. */
export class ApiUnavailable extends Error {
    constructor() {
        super("backend no disponible");
        this.name = "ApiUnavailable";
    }
}

/** El backend respondió con un status de error (401, 404, 500…). */
export class ApiError extends Error {
    status: number;
    constructor(status: number, message = `error ${status}`) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

async function request<T>(path: string, token?: string | null, init?: RequestInit): Promise<T> {
    let res: Response;
    try {
        res = await fetch(`${API_URL}${path}`, {
            ...init,
            signal: AbortSignal.timeout(TIMEOUT_MS),
            headers: {
                ...(init?.body ? { "Content-Type": "application/json" } : {}),
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
                ...init?.headers,
            },
        });
    } catch {
        throw new ApiUnavailable();
    }
    if (!res.ok) throw new ApiError(res.status);
    if (res.status === 204) return undefined as T;
    return (await res.json()) as T;
}

export function apiGet<T>(path: string, token?: string | null): Promise<T> {
    return request<T>(path, token);
}

export function apiPost<T>(path: string, body: unknown, token?: string | null): Promise<T> {
    return request<T>(path, token, { method: "POST", body: JSON.stringify(body) });
}

// ---- Auth (Endpoints/AuthEndpoints.cs, Dtos/Auth/AuthDtos.cs) ----

export interface UsuarioDto {
    idUser: number;
    name: string;
    email: string;
    locale: string;
    status: string;
    createdAt: string;
}

export interface AuthResponse {
    token: string;
    expiresAtUtc: string;
    user: UsuarioDto;
}

export function loginRequest(email: string, password: string): Promise<AuthResponse> {
    return request<AuthResponse>("/auth/login", null, {
        method: "POST",
        body: JSON.stringify({ email, password }),
    });
}

// ---- DTOs (espejo camelCase de los records del backend) ----

export interface AccountResponse {
    idAccount: number;
    accountType: string;
    alias: string;
    maskedNumber: string;
    currency: string;
    balance: number;
    status: string;
    createdAt: string;
}

export interface AccountSummaryResponse {
    totalBalance: number;
    currency: string;
    accounts: AccountResponse[];
}

export interface TransactionResponse {
    idTransaction: number;
    idAccount: number;
    date: string; // yyyy-mm-dd
    amount: number;
    direction: string; // credit | debit
    category: string;
    description: string;
    status: string; // posted | pending | failed
    reference: string;
    idExpenseCategory?: number | null;
}

export interface DailyBalanceResponse {
    idBalance: number;
    date: string;
    openingBalance: number;
    income: number;
    expenses: number;
    closingBalance: number;
}

export interface StatementResponse {
    idStatement: number;
    idAccount: number;
    cutOffDay: number;
    periodStart: string;
    periodEnd: string;
    openingBalance: number;
    closingBalance: number;
    totalCredits: number;
    totalDebits: number;
    transactionCount: number;
    accountType: string;
    status: string;
    generatedAt: string;
}

export interface CreditCardResponse {
    idCreditCard: number;
    cardNumberMasked: string;
    cardType: string;
    creditLimit: number;
    availableCredit: number;
    interestRate: number;
    statementCutOffDay: number;
    paymentDueDay: number;
    status: string;
    createdAt: string;
}

export interface BudgetResponse {
    idBudget: number;
    idExpenseCategory: number;
    categoryName: string;
    categoryCode: string;
    month: number;
    year: number;
    amountLimit: number;
    currentSpent: number;
    usagePercent: number;
    status: string;
}

export interface BudgetMonthlySummaryResponse {
    month: number;
    year: number;
    totalLimit: number;
    totalSpent: number;
    budgets: BudgetResponse[];
}

export interface SavingsGoalResponse {
    idGoal: number;
    name: string;
    targetAmount: number;
    currentAmount: number;
    progressPercent: number;
    targetDate: string;
    status: string;
    createdAt: string;
    updatedAt: string;
}

export interface ReconciliationResponse {
    idMatch: number;
    idTransfer: number;
    idTransaction: number;
    status: string;
    matchScore: number;
    matchedAt: string | null;
    notes: string;
}

export interface TransferResponse {
    idTransfer: number;
    idOriginAccount: number;
    destinationAlias: string;
    destinationMasked: string;
    amount: number;
    currency: string;
    concept: string;
    status: string;
    idempotencyKey: string;
    createdAt: string;
    confirmedAt: string | null;
}

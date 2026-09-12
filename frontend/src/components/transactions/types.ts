export type TransactionDirection = "in" | "out";
export type TransactionStatus = "completed" | "pending" | "failed";
export type TransactionCategory =
    | "transfer"
    | "payment"
    | "subscription"
    | "income"
    | "withdrawal"
    | "other";

export interface Transaction {
    id: string;
    accountId: string;
    date: string; // ISO yyyy-mm-dd
    amount: number;
    direction: TransactionDirection;
    category: TransactionCategory;
    description: string;
    status: TransactionStatus;
    reference: string;
}

export interface TransactionFiltersState {
    accountId: string; // "all" | account id
    direction: "all" | TransactionDirection;
    category: "all" | TransactionCategory;
    dateFrom: string; // "" si no aplica
    dateTo: string;
}

export const DEFAULT_FILTERS: TransactionFiltersState = {
    accountId: "all",
    direction: "all",
    category: "all",
    dateFrom: "",
    dateTo: "",
};

export const CATEGORY_LABELS: Record<TransactionCategory, string> = {
    transfer: "Transferencia",
    payment: "Pago",
    subscription: "Suscripción",
    income: "Ingreso",
    withdrawal: "Retiro",
    other: "Otro",
};

export const STATUS_LABELS: Record<TransactionStatus, string> = {
    completed: "Completada",
    pending: "Pendiente",
    failed: "Fallida",
};

// Mismos ids de cuenta que balance/types.ts (acc-1, acc-2, acc-3)
export const TRANSACTION_ACCOUNTS = [
    { id: "acc-1", alias: "Cuenta Nómina" },
    { id: "acc-2", alias: "Cuenta Ahorro" },
    { id: "acc-3", alias: "Cuenta Tarjeta" },
];

export function formatCurrency(amount: number): string {
    return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency: "MXN",
    }).format(amount);
}

export const MOCK_TRANSACTIONS: Transaction[] = [
    {
        id: "tx-001",
        accountId: "acc-1",
        date: "2026-09-10",
        amount: 15000,
        direction: "in",
        category: "income",
        description: "Depósito de nómina",
        status: "completed",
        reference: "REF-1001",
    },
    {
        id: "tx-002",
        accountId: "acc-1",
        date: "2026-09-09",
        amount: 450.5,
        direction: "out",
        category: "subscription",
        description: "Suscripción streaming",
        status: "completed",
        reference: "REF-1002",
    },
    {
        id: "tx-003",
        accountId: "acc-2",
        date: "2026-09-08",
        amount: 2000,
        direction: "out",
        category: "transfer",
        description: "Transferencia a Cuenta Tarjeta",
        status: "completed",
        reference: "REF-1003",
    },
    {
        id: "tx-004",
        accountId: "acc-3",
        date: "2026-09-08",
        amount: 2000,
        direction: "in",
        category: "transfer",
        description: "Transferencia recibida",
        status: "completed",
        reference: "REF-1004",
    },
    {
        id: "tx-005",
        accountId: "acc-3",
        date: "2026-09-07",
        amount: 890.25,
        direction: "out",
        category: "payment",
        description: "Pago servicio de luz",
        status: "pending",
        reference: "REF-1005",
    },
    {
        id: "tx-006",
        accountId: "acc-2",
        date: "2026-09-05",
        amount: 300,
        direction: "out",
        category: "withdrawal",
        description: "Retiro en cajero",
        status: "failed",
        reference: "REF-1006",
    },
    {
        id: "tx-007",
        accountId: "acc-1",
        date: "2026-09-03",
        amount: 1250.75,
        direction: "out",
        category: "other",
        description: "Compra en línea",
        status: "completed",
        reference: "REF-1007",
    },
];
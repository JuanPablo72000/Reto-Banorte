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

// Mismos ids de cuenta que balance/types.ts (seed rico: 4 cuentas)
export const TRANSACTION_ACCOUNTS = [
    { id: "acc-1", alias: "Nómina" },
    { id: "acc-2", alias: "Ahorro" },
    { id: "acc-3", alias: "Compras en línea" },
    { id: "acc-4", alias: "Cuenta antigua" },
];

export function formatCurrency(amount: number): string {
    return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency: "MXN",
    }).format(amount);
}

// Congruente con DbSeeder.cs / mock_data.py: mismas cuentas, vocabulario y
// descripciones del ledger (nómina quincenal, traspasos, suscripciones…).
export const MOCK_TRANSACTIONS: Transaction[] = [
    {
        id: "tx-001",
        accountId: "acc-1",
        date: "2026-09-11",
        amount: 24500,
        direction: "in",
        category: "income",
        description: "Pago nómina quincenal",
        status: "completed",
        reference: "NOM-0001",
    },
    {
        id: "tx-002",
        accountId: "acc-1",
        date: "2026-09-10",
        amount: 1450,
        direction: "out",
        category: "other",
        description: "Walmart Express",
        status: "completed",
        reference: "SUP-0002",
    },
    {
        id: "tx-003",
        accountId: "acc-1",
        date: "2026-09-10",
        amount: 185.5,
        direction: "out",
        category: "transfer",
        description: "Uber",
        status: "completed",
        reference: "UBER-0003",
    },
    {
        id: "tx-004",
        accountId: "acc-1",
        date: "2026-09-09",
        amount: 890.75,
        direction: "out",
        category: "payment",
        description: "Sushi Roll",
        status: "completed",
        reference: "REST-0005",
    },
    {
        id: "tx-005",
        accountId: "acc-1",
        date: "2026-09-07",
        amount: 229,
        direction: "out",
        category: "subscription",
        description: "Netflix premium",
        status: "completed",
        reference: "NFLX-0008",
    },
    {
        id: "tx-006",
        accountId: "acc-1",
        date: "2026-09-04",
        amount: 2000,
        direction: "out",
        category: "transfer",
        description: "Transferencia a Mamá — apoyo mensual",
        status: "completed",
        reference: "TEXT1",
    },
    {
        id: "tx-007",
        accountId: "acc-1",
        date: "2026-09-03",
        amount: 8500,
        direction: "out",
        category: "payment",
        description: "Renta departamento",
        status: "completed",
        reference: "REN-0015",
    },
    {
        id: "tx-008",
        accountId: "acc-1",
        date: "2026-09-02",
        amount: 3000,
        direction: "out",
        category: "transfer",
        description: "Traspaso a Ahorro — meta mensual",
        status: "completed",
        reference: "TRA-0019",
    },
    {
        id: "tx-009",
        accountId: "acc-2",
        date: "2026-09-02",
        amount: 3000,
        direction: "in",
        category: "transfer",
        description: "Traspaso desde Nómina — meta mensual",
        status: "completed",
        reference: "TRA-0030",
    },
    {
        id: "tx-010",
        accountId: "acc-2",
        date: "2026-09-01",
        amount: 512.4,
        direction: "in",
        category: "income",
        description: "Intereses mensuales cuenta ahorro",
        status: "completed",
        reference: "INT-0031",
    },
    {
        id: "tx-011",
        accountId: "acc-3",
        date: "2026-09-01",
        amount: 640,
        direction: "out",
        category: "other",
        description: "Compra en línea Amazon",
        status: "completed",
        reference: "AMZ-0033",
    },
    {
        id: "tx-012",
        accountId: "acc-3",
        date: "2026-08-31",
        amount: 145,
        direction: "in",
        category: "income",
        description: "Cashback programa de recompensas",
        status: "completed",
        reference: "CSH-0034",
    },
    {
        id: "tx-013",
        accountId: "acc-1",
        date: "2026-09-12",
        amount: 1450,
        direction: "out",
        category: "other",
        description: "Walmart Express (en proceso)",
        status: "pending",
        reference: "SUP-0026",
    },
    {
        id: "tx-014",
        accountId: "acc-1",
        date: "2026-09-09",
        amount: 1200,
        direction: "out",
        category: "other",
        description: "Compra declinada por el comercio",
        status: "failed",
        reference: "FALL-0028",
    },
    {
        id: "tx-015",
        accountId: "acc-1",
        date: "2026-09-06",
        amount: 4500,
        direction: "out",
        category: "transfer",
        description: "Transferencia devuelta — cuenta destino incorrecta",
        status: "failed",
        reference: "TDEV-0029",
    },
];
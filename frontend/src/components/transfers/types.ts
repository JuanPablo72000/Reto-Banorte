// components/transfers/types.ts
// NOTA: esto es un mock rápido para el prototipo. Cuando exista lib/types.ts
// real (conectado a Cain), estos tipos deberían moverse/alinearse ahí.

export type TransferStatus =
    | "draft"
    | "pending_confirmation"
    | "confirmed"
    | "failed"
    | "expired"
    | "cancelled";

export interface MockAccount {
    id: string;
    label: string;
    accountNumber: string; // ya enmascarado, ej. "**** 4821"
    balance: number;
    currency: string;
}

export interface TransferDraft {
    fromAccountId: string;
    toAccountId: string;
    amount: number;
    note: string;
}

// Cuentas ficticias para el prototipo
export const MOCK_ACCOUNTS: MockAccount[] = [
    {
        id: "acc-1",
        label: "Cuenta Nómina",
        accountNumber: "**** 4821",
        balance: 18450.32,
        currency: "MXN",
    },
    {
        id: "acc-2",
        label: "Cuenta Ahorro",
        accountNumber: "**** 1190",
        balance: 52310.0,
        currency: "MXN",
    },
    {
        id: "acc-3",
        label: "Cuenta Juan Pablo R.",
        accountNumber: "**** 7765",
        balance: 0,
        currency: "MXN",
    },
];

export function formatCurrency(amount: number, currency = "MXN") {
    return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency,
    }).format(amount);
}
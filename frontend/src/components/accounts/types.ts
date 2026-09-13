import { AccountBalance, MOCK_BALANCES } from "@/components/balance/types";

export type AccountType = "checking" | "savings" | "credit";
export type AccountStatus = "active" | "blocked" | "closed";

export interface AccountMeta {
    accountType: AccountType;
    status: AccountStatus;
    createdAt: string; // ISO yyyy-mm-dd
}

export type AccountWithMeta = AccountBalance & AccountMeta;

export const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
    checking: "Cuenta Corriente",
    savings: "Cuenta de Ahorro",
    credit: "Tarjeta de Crédito",
};

export const ACCOUNT_STATUS_LABELS: Record<AccountStatus, string> = {
    active: "Activa",
    blocked: "Bloqueada",
    closed: "Cerrada",
};

// Metadata adicional por cuenta, keyed por el mismo id que usa balance/MOCK_BALANCES.
// Refleja las 4 cuentas del seed rico (DbSeeder.cs / mock_data.py).
const ACCOUNT_META: Record<string, AccountMeta> = {
    "acc-1": {
        accountType: "checking",
        status: "active",
        createdAt: "2026-06-15",
    },
    "acc-2": {
        accountType: "savings",
        status: "active",
        createdAt: "2026-06-15",
    },
    "acc-3": {
        accountType: "checking",
        status: "active",
        createdAt: "2026-08-13",
    },
    "acc-4": {
        accountType: "checking",
        status: "blocked",
        createdAt: "2024-10-13",
    },
};

export function getAccountsWithMeta(): AccountWithMeta[] {
    return MOCK_BALANCES.map((account) => ({
        ...account,
        ...ACCOUNT_META[account.id],
    }));
}

export function getAccountWithMetaById(id: string): AccountWithMeta | undefined {
    return getAccountsWithMeta().find((account) => account.id === id);
}
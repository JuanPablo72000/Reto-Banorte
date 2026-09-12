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
// TODO(unificación futura): cuando exista lib/types.ts central, esto se une
// directo al objeto de cuenta que devuelva Cain.
const ACCOUNT_META: Record<string, AccountMeta> = {
    "acc-1": {
        accountType: "checking",
        status: "active",
        createdAt: "2023-02-14",
    },
    "acc-2": {
        accountType: "savings",
        status: "active",
        createdAt: "2022-11-01",
    },
    "acc-3": {
        accountType: "credit",
        status: "blocked",
        createdAt: "2024-06-20",
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
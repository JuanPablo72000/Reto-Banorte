// components/balance/types.ts
// Mock de datos para el prototipo. Cuando exista lib/cain-client.ts real,
// esto se reemplaza por la respuesta de GET /accounts (o equivalente).

export interface BalanceTrendPoint {
    day: string; // etiqueta corta, ej. "Lun", "01/09"
    balance: number;
    [key: string]: string | number;
}

export interface AccountBalance {
    id: string;
    label: string;
    accountNumber: string; // enmascarado, ej. "**** 4821"
    currency: string;
    currentBalance: number;
    trend: BalanceTrendPoint[]; // últimos N días, mock
}

export function formatCurrency(amount: number, currency = "MXN") {
    return new Intl.NumberFormat("es-MX", {
        style: "currency",
        currency,
    }).format(amount);
}

// 7 días de historial ficticio por cuenta
export const MOCK_BALANCES: AccountBalance[] = [
    {
        id: "acc-1",
        label: "Cuenta Nómina",
        accountNumber: "**** 4821",
        currency: "MXN",
        currentBalance: 18450.32,
        trend: [
            { day: "Lun", balance: 15200 },
            { day: "Mar", balance: 16100 },
            { day: "Mié", balance: 15800 },
            { day: "Jue", balance: 17200 },
            { day: "Vie", balance: 19500 },
            { day: "Sáb", balance: 18900 },
            { day: "Dom", balance: 18450.32 },
        ],
    },
    {
        id: "acc-2",
        label: "Cuenta Ahorro",
        accountNumber: "**** 1190",
        currency: "MXN",
        currentBalance: 52310.0,
        trend: [
            { day: "Lun", balance: 50000 },
            { day: "Mar", balance: 50000 },
            { day: "Mié", balance: 50500 },
            { day: "Jue", balance: 51000 },
            { day: "Vie", balance: 51000 },
            { day: "Sáb", balance: 51800 },
            { day: "Dom", balance: 52310.0 },
        ],
    },
    {
        id: "acc-3",
        label: "Cuenta Juan Pablo R.",
        accountNumber: "**** 7765",
        currency: "MXN",
        currentBalance: 0,
        trend: [
            { day: "Lun", balance: 200 },
            { day: "Mar", balance: 150 },
            { day: "Mié", balance: 90 },
            { day: "Jue", balance: 40 },
            { day: "Vie", balance: 10 },
            { day: "Sáb", balance: 0 },
            { day: "Dom", balance: 0 },
        ],
    },
];
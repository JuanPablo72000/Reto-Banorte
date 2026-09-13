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

// 7 días de historial ficticio por cuenta — congruente con el seed rico del
// backend (DbSeeder.cs) y con el mock del MCP (mock_data.py): mismas 4
// cuentas, mismos saldos finales.
export const MOCK_BALANCES: AccountBalance[] = [
    {
        id: "acc-1",
        label: "Nómina",
        accountNumber: "**** 1234",
        currency: "MXN",
        currentBalance: 58024.65,
        trend: [
            { day: "Lun", balance: 53200 },
            { day: "Mar", balance: 54100 },
            { day: "Mié", balance: 53800 },
            { day: "Jue", balance: 55200 },
            { day: "Vie", balance: 56900 },
            { day: "Sáb", balance: 57400 },
            { day: "Dom", balance: 58024.65 },
        ],
    },
    {
        id: "acc-2",
        label: "Ahorro",
        accountNumber: "**** 4321",
        currency: "MXN",
        currentBalance: 103036.06,
        trend: [
            { day: "Lun", balance: 100857 },
            { day: "Mar", balance: 101200 },
            { day: "Mié", balance: 101200 },
            { day: "Jue", balance: 101650 },
            { day: "Vie", balance: 102100 },
            { day: "Sáb", balance: 102600 },
            { day: "Dom", balance: 103036.06 },
        ],
    },
    {
        id: "acc-3",
        label: "Compras en línea",
        accountNumber: "**** 7788",
        currency: "MXN",
        currentBalance: 3617.83,
        trend: [
            { day: "Lun", balance: 4800 },
            { day: "Mar", balance: 4650 },
            { day: "Mié", balance: 4400 },
            { day: "Jue", balance: 4100 },
            { day: "Vie", balance: 3900 },
            { day: "Sáb", balance: 3750 },
            { day: "Dom", balance: 3617.83 },
        ],
    },
    {
        id: "acc-4",
        label: "Cuenta antigua",
        accountNumber: "**** 0002",
        currency: "MXN",
        currentBalance: 0,
        trend: [
            { day: "Lun", balance: 0 },
            { day: "Mar", balance: 0 },
            { day: "Mié", balance: 0 },
            { day: "Jue", balance: 0 },
            { day: "Vie", balance: 0 },
            { day: "Sáb", balance: 0 },
            { day: "Dom", balance: 0 },
        ],
    },
];
export type ReconciliationStatus = "pending" | "matched" | "mismatch";

export interface ReconciliationMatch {
    id: string;
    transferId: string;
    transactionId: string | null; // null si aún no aparece (pending)
    status: ReconciliationStatus;
    matchScore: number | null; // 0-1, null si pending
    matchedAt: string | null; // ISO date, null si pending
    notes: string;
}

export const RECONCILIATION_STATUS_LABELS: Record<ReconciliationStatus, string> = {
    pending: "Pendiente",
    matched: "Conciliada",
    mismatch: "Discrepancia",
};

// Mock de datos para el prototipo. Cuando exista lib/cain-client.ts real,
// esto se reemplaza por la respuesta de GET /reconciliation.
export const MOCK_RECONCILIATION_MATCHES: ReconciliationMatch[] = [
    {
        id: "rec-001",
        transferId: "tr-1001",
        transactionId: "tx-003",
        status: "matched",
        matchScore: 1.0,
        matchedAt: "2026-09-08",
        notes: "Coincidencia exacta de monto y fecha",
    },
    {
        id: "rec-002",
        transferId: "tr-1002",
        transactionId: null,
        status: "pending",
        matchScore: null,
        matchedAt: null,
        notes: "Transacción aún no aparece en el sistema",
    },
    {
        id: "rec-003",
        transferId: "tr-1003",
        transactionId: "tx-005",
        status: "mismatch",
        matchScore: 0.62,
        matchedAt: "2026-09-07",
        notes: "Monto no coincide: transferencia $890.00 vs transacción $890.25",
    },
    {
        id: "rec-004",
        transferId: "tr-1004",
        transactionId: "tx-004",
        status: "matched",
        matchScore: 0.98,
        matchedAt: "2026-09-08",
        notes: "Coincidencia con diferencia mínima de horario",
    },
    {
        id: "rec-005",
        transferId: "tr-1005",
        transactionId: null,
        status: "pending",
        matchScore: null,
        matchedAt: null,
        notes: "En espera de sincronización nocturna",
    },
];
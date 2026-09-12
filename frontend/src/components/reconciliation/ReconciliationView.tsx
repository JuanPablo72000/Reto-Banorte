"use client";

import { ReconciliationTable } from "./ReconciliationTable";
import { MOCK_RECONCILIATION_MATCHES } from "./types";

export function ReconciliationView() {
    return (
        <section className="flex flex-col gap-6">
            <h2 className="text-xl font-semibold text-[var(--color-text)]">
                Conciliación de transferencias
            </h2>
            <ReconciliationTable matches={MOCK_RECONCILIATION_MATCHES} />
        </section>
    );
}
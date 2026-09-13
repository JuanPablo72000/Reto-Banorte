"use client";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { estadoRelevante, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { lista, mxn } from "@/lib/plan-result";

interface Cuenta {
    id_account: number;
    alias: string;
    account_type: string;
    masked_number: string;
    balance: number;
    currency: string;
    status: string;
}

// get_accounts (summary/table).
export function AccountsPlanList({ step }: { step: ExecutedStep }) {
    const rows = lista<Cuenta>(step.result);
    return (
        <div className="flex flex-col gap-2">
            {rows.map((c) => (
                <Card key={c.id_account}>
                    <div className="flex items-center justify-between gap-2">
                        <div>
                            <p className="font-medium text-[var(--color-text)]">
                                {c.alias} <span className="text-[var(--color-text-muted)]">{c.masked_number}</span>
                            </p>
                            <p className="text-xs text-[var(--color-text-muted)]">{c.account_type}</p>
                        </div>
                        <div className="text-right">
                            <p className="font-semibold">{mxn(c.balance, c.currency)}</p>
                            {estadoRelevante(c.status) && (
                                <Badge tone={tonoEstado(c.status)}>{etiquetaEstado(c.status)}</Badge>
                            )}
                        </div>
                    </div>
                </Card>
            ))}
        </div>
    );
}

"use client";

import { Badge } from "@/components/ui/Badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { campo, lista, mxn, objeto } from "@/lib/plan-result";
import { attrsAnimacion } from "@/lib/atributos";

interface Cuenta {
    alias: string;
    masked_number: string;
    balance: number;
    currency: string;
}

// get_account_summary (summary) — cifra protagonista + desglose por
// cuenta (diseño HeroStat de Qwen adaptado a AccountSummaryResponse).
export function AccountSummaryCard({ step, indice = 0 }: { step: ExecutedStep; indice?: number }) {
    const d = objeto<Record<string, unknown>>(step.result);
    if (!d) return null;
    const moneda = campo<string>(d, "currency", "MXN");
    const cuentas = lista<Cuenta>(Array.isArray(d.accounts) ? d.accounts : undefined);

    return (
        <section aria-label="Saldo total" {...attrsAnimacion(step.visual.animation, indice)}>
            <Card>
                <CardHeader>
                    <CardTitle className="text-base font-medium text-[var(--color-text-muted)]">
                        Saldo total
                    </CardTitle>
                </CardHeader>
                <p
                    className="text-4xl font-semibold tracking-tight text-[var(--color-text)] tabular-nums"
                    aria-live="polite"
                >
                    {mxn(campo<number>(d, "total_balance", 0), moneda)}
                </p>
                {cuentas.length > 0 && (
                    <dl className="mt-3 grid grid-cols-3 gap-[var(--gap-item)] text-center text-sm max-sm:grid-cols-1 max-sm:text-left">
                        {cuentas.map((c) => (
                            <div
                                key={`${c.alias}-${c.masked_number}`}
                                className="rounded-lg bg-[var(--color-surface-2)] p-[var(--pad-card)]"
                            >
                                <dt className="text-[var(--color-text-muted)]">
                                    {c.alias} {c.masked_number}
                                </dt>
                                <dd className="font-semibold tabular-nums text-[var(--color-text)]">
                                    {mxn(c.balance, c.currency ?? moneda)}
                                </dd>
                            </div>
                        ))}
                    </dl>
                )}
                {cuentas.length > 0 && (
                    <p className="mt-2">
                        <Badge tone="info">
                            {cuentas.length} {cuentas.length === 1 ? "cuenta" : "cuentas"}
                        </Badge>
                    </p>
                )}
            </Card>
        </section>
    );
}

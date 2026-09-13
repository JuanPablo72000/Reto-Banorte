"use client";

import { Badge } from "@/components/ui/Badge";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Table } from "@/components/ui/Table";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { estadoRelevante, etiquetaEstado, tonoEstado } from "@/lib/etiquetas";
import { lista, mxn } from "@/lib/plan-result";

interface Tarjeta {
    id_credit_card: number;
    card_number_masked: string;
    card_type?: string | null;
    credit_limit: number;
    available_credit: number;
    interest_rate: number;
    status: string;
}

// get_credit_cards (table). Muestra lo que importa: cuánto debes (deuda),
// qué % del límite usas y la tasa; el estado solo si requiere atención.
export function CreditCardsTable({ step }: { step: ExecutedStep }) {
    const rows = lista<Tarjeta>(step.result);
    const mostrarEstado = rows.some((c) => estadoRelevante(c.status));
    return (
        <Table
            caption="Tarjetas de crédito"
            columns={[
                { key: "num", header: "Tarjeta", render: (c) => `${c.card_number_masked} ${c.card_type ?? ""}`.trim() },
                {
                    key: "deuda",
                    header: "Debes",
                    align: "right",
                    render: (c) => mxn(c.credit_limit - c.available_credit),
                },
                {
                    key: "uso",
                    header: "Uso",
                    render: (c) => (
                        <ProgressBar
                            value={c.credit_limit - c.available_credit}
                            max={c.credit_limit || 1}
                            tone={c.available_credit < c.credit_limit * 0.2 ? "danger" : "neutral"}
                        />
                    ),
                },
                { key: "tasa", header: "Tasa %", align: "right", render: (c) => `${c.interest_rate}%` },
                ...(mostrarEstado
                    ? [
                          {
                              key: "status",
                              header: "Estado",
                              render: (c: Tarjeta) => (
                                  <Badge tone={tonoEstado(c.status)}>{etiquetaEstado(c.status)}</Badge>
                              ),
                          },
                      ]
                    : []),
            ]}
            data={rows}
            getRowId={(c) => c.id_credit_card}
        />
    );
}

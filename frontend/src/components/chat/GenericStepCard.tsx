"use client";

import { EmptyState } from "@/components/states/EmptyState";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { esClaveVisible, etiquetaCategoria } from "@/lib/etiquetas";

// Fallback honesto para tools sin componente dedicado (ej.
// search_memory_context): muestra el mensaje del plan y un resumen del
// resultado solo con campos legibles (sin ids ni claves técnicas).
// Nunca datos mock.
export function GenericStepCard({ step }: { step: ExecutedStep }) {
    const r = step.result as
        | { total: number; muestra: Record<string, unknown>[] }
        | Record<string, unknown>
        | undefined;
    const filas =
        r && typeof r === "object" && !Array.isArray(r) && Array.isArray(r.muestra)
            ? r.muestra.slice(0, 3)
            : [];
    if (filas.length === 0) {
        return (
            <EmptyState
                title="Sin resultados"
                description="No hay datos para mostrar en este paso."
            />
        );
    }
    return (
        <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-sm">
            <ul className="flex flex-col gap-1">
                {filas.map((f, i) => (
                    <li key={i} className="truncate text-[var(--color-text)]">
                        {Object.entries(f)
                            .filter(([k, v]) => esClaveVisible(k) && typeof v !== "object")
                            .slice(0, 4)
                            .map(([k, v]) =>
                                k === "category"
                                    ? String(etiquetaCategoria(v))
                                    : `${k}: ${String(v)}`,
                            )
                            .join(" · ") || "—"}
                    </li>
                ))}
            </ul>
        </div>
    );
}

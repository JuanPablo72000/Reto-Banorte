"use client";

import { useId, useMemo } from "react";
import { Icon } from "@/components/ui/Icon";
import type { SuggestedAction, Variant } from "@/lib/types/action-plan";

// Sugerencias del plan como pills (sin reordenado con arrastre): entran una
// a una en cascada, con icono + tooltip. Máximo un primary (se degrada el
// resto a secondary); usa variant/icon que manda la IA.
export function SuggestionBar({
    sugerencias,
    onActivar,
    etiqueta = "Sugerencias",
}: {
    sugerencias: readonly SuggestedAction[];
    onActivar: (s: SuggestedAction) => void;
    etiqueta?: string;
}) {
    const uid = useId();

    const normalizadas = useMemo(() => {
        const idxPrimera = sugerencias.findIndex((s) => (s.variant ?? "secondary") === "primary");
        return sugerencias.map((s, i) => {
            const v: Variant = s.variant ?? "secondary";
            return { ...s, variant: v === "primary" && i !== idxPrimera ? ("secondary" as Variant) : v };
        });
    }, [sugerencias]);

    if (normalizadas.length === 0) return null;

    return (
        <section aria-label={etiqueta}>
            <div className="flex flex-wrap gap-2">
                {normalizadas.map((s, i) => {
                    const tipId = `${uid}-tip-${s.action_id}`;
                    return (
                        <div
                            key={s.action_id}
                            className="group relative"
                            style={{ "--orden": i + 1 } as React.CSSProperties}
                        >
                            <button
                                type="button"
                                onClick={() => onActivar(s)}
                                aria-describedby={tipId}
                                title={s.description}
                                className={[
                                    "ui-pop flex min-h-[var(--target-min)] items-center gap-2 rounded-full border px-4 text-base font-medium",
                                    "shadow-[var(--shadow-1)] transition-[transform,background-color,box-shadow] duration-150 motion-reduce:transition-none",
                                    "hover:-translate-y-0.5 hover:shadow-[var(--shadow-2)] active:translate-y-0 active:scale-[0.98]",
                                    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]",
                                    s.variant === "primary"
                                        ? "border-transparent bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                        : s.variant === "danger"
                                          ? "border-transparent bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]"
                                          : s.variant === "ghost"
                                            ? "border-transparent bg-transparent text-[var(--color-text)]"
                                            : "border-[var(--color-border-subtle)] bg-[var(--color-surface-2)] text-[var(--color-text)] hover:bg-[var(--color-surface-3)]",
                                ].join(" ")}
                            >
                                <Icon name={s.icon} size={18} />
                                <span className="whitespace-nowrap">{s.label}</span>
                            </button>
                            <span
                                id={tipId}
                                role="tooltip"
                                className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 hidden w-max max-w-60 -translate-x-1/2 rounded-md border border-[var(--color-border-subtle)] bg-[var(--color-surface-3)] px-2 py-1 text-xs text-[var(--color-text)] shadow-[var(--shadow-1)] group-hover:block group-focus-within:block"
                            >
                                {s.description}
                            </span>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}

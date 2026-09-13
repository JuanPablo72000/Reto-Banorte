"use client";

import { useId, useMemo } from "react";
import { MovableZone } from "@/components/chat/MovableZone";
import type { MovableZoneContext } from "@/components/chat/MovableZone";
import { Icon } from "@/components/ui/Icon";
import { attrsAnimacion } from "@/lib/atributos";
import type { SuggestedAction, Variant } from "@/lib/types/action-plan";

// Sugerencias del plan como pills movibles (arrastrar para reordenar,
// orden persistido) con icono + tooltip. Máximo un primary (se degrada
// el resto a secondary); usa variant/tone/icon que manda la IA.
export function SuggestionBar({
    sugerencias,
    onActivar,
    storageKey = "sugerencias-orden",
    etiqueta = "Sugerencias",
    animacion,
    orden = 0,
}: {
    sugerencias: readonly SuggestedAction[];
    onActivar: (s: SuggestedAction) => void;
    storageKey?: string;
    etiqueta?: string;
    animacion?: string | null;
    orden?: number;
}) {
    const uid = useId();

    const normalizadas = useMemo(() => {
        const idxPrimera = sugerencias.findIndex((s) => (s.variant ?? "secondary") === "primary");
        return sugerencias.map((s, i) => {
            const v: Variant = s.variant ?? "secondary";
            return { ...s, variant: v === "primary" && i !== idxPrimera ? ("secondary" as Variant) : v };
        });
    }, [sugerencias]);

    const attrs = attrsAnimacion(animacion, orden);
    if (normalizadas.length === 0) return null;

    return (
        <section aria-label={etiqueta} {...attrs}>
            <div className="overflow-x-auto pb-2 snap-x snap-mandatory lg:overflow-visible">
                <MovableZone
                    items={normalizadas.map((s) => ({ ...s, id: s.action_id }))}
                    storageKey={storageKey}
                    orientation="horizontal"
                    etiquetaItem="Sugerencia"
                    label={`${etiqueta}: arrastrables para reordenar`}
                    className="!gap-2"
                >
                    {(s, _i, ctx: MovableZoneContext) => {
                        const tipId = `${uid}-tip-${s.action_id}`;
                        return (
                            <div className="group relative flex shrink-0 snap-start items-stretch rounded-full shadow-[var(--shadow-1)] bg-[var(--color-surface-2)] border border-[var(--color-border-subtle)]">
                                <button
                                    type="button"
                                    aria-label={ctx.handleAriaLabel}
                                    aria-grabbed={ctx.grabbed}
                                    {...ctx.handleProps}
                                    className="flex w-11 min-h-[var(--target-min)] items-center justify-center rounded-l-full text-[var(--color-text-muted)] hover:bg-[var(--color-surface-3)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] cursor-grab active:cursor-grabbing touch-none"
                                >
                                    <Icon name="grip" size={18} />
                                </button>
                                <button
                                    type="button"
                                    onClick={() => onActivar(s)}
                                    aria-describedby={tipId}
                                    title={s.description}
                                    className={`flex min-h-[var(--target-min)] items-center gap-2 rounded-r-full pr-4 pl-1 text-base font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2 ${
                                        s.variant === "primary"
                                            ? "bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                            : s.variant === "danger"
                                              ? "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]"
                                              : s.variant === "ghost"
                                                ? "bg-transparent text-[var(--color-text)]"
                                                : "bg-[var(--color-surface-2)] text-[var(--color-text)]"
                                    }`}
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
                    }}
                </MovableZone>
            </div>
        </section>
    );
}

"use client";

import { Icon } from "@/components/ui/Icon";
import type { IconType, Tone } from "@/lib/types/action-plan";

export interface CompactRowProps {
    label: string;
    value: string;
    href?: string;
    onClick?: () => void;
    description?: string;
    icon?: IconType;
    tone?: Tone;
}

const TONOS: Record<string, string> = {
    success: "text-[var(--color-success-text)]",
    warning: "text-[var(--color-warning-text)]",
    danger: "text-[var(--color-danger-text)]",
    info: "text-[var(--color-info-text)]",
    neutral: "text-[var(--color-text-muted)]",
};

/** Fila densa para sidebar/perfil. Interactiva si hay href/onClick;
 *  siempre ≥44px aunque la densidad sea compacta. */
export function CompactRow({
    label,
    value,
    href,
    onClick,
    description,
    icon = "info",
    tone = "neutral",
}: CompactRowProps) {
    const clases =
        "flex w-full items-center gap-2 min-h-[var(--target-min)] px-2 rounded-lg text-left hover:bg-[var(--color-surface-3)] active:scale-[0.99] motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]";
    const contenido = (
        <>
            <span aria-hidden="true" className={TONOS[tone] ?? TONOS.neutral}>
                <Icon name={icon} size={18} />
            </span>
            <span className="flex-1 truncate text-base text-[var(--color-text)]">{label}</span>
            {description && (
                <span className="hidden text-sm text-[var(--color-text-muted)] lg:inline">{description}</span>
            )}
            <span className="ml-auto shrink-0 text-sm font-semibold tabular-nums text-[var(--color-text)]">
                {value}
            </span>
        </>
    );
    return (
        <li>
            {href ? (
                <a href={href} className={clases} aria-label={`${label}: ${value}`}>
                    {contenido}
                </a>
            ) : onClick ? (
                <button type="button" onClick={onClick} className={clases} aria-label={`${label}: ${value}`}>
                    {contenido}
                </button>
            ) : (
                <div className={`${clases} hover:bg-transparent`}>{contenido}</div>
            )}
        </li>
    );
}

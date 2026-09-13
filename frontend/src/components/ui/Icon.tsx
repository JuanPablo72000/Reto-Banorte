"use client";

import type { IconType, Tone } from "@/lib/types/action-plan";

export interface IconProps {
    name: IconType | IconExtra;
    tone?: Tone | null;
    className?: string;
    size?: number;
    title?: string;
}

// Extras internos (grips de reordenado, estados, envíos): NO vienen del
// plan, solo de la UI. Traídos del set de Qwen.
export type IconExtra = "grip" | "plus" | "check" | "clock" | "bell" | "lock" | "send" | "chart";

// Set inline de iconos stroke (24x24, currentColor) para los 15 IconType
// del plan. Sin dependencias, con aria-hidden (decorativos: el texto
// accesible ya viene en messages/aria_label del plan).
const PATHS: Record<IconType, React.ReactNode> = {
    account: (<><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5" /></>),
    transaction: (<><path d="M4 7h13l-3-3M20 17H7l3 3" /></>),
    transfer: (<><path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" /></>),
    balance: (<><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M2 10h20M6 15h4" /></>),
    search: (<><circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" /></>),
    help: (<><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.1.9-1.1 1.8" /><circle cx="12" cy="17" r="0.5" fill="currentColor" /></>),
    warning: (<><path d="M12 3 2 21h20L12 3z" /><path d="M12 10v5" /><circle cx="12" cy="18" r="0.5" fill="currentColor" /></>),
    success: (<><circle cx="12" cy="12" r="9" /><path d="m8.5 12.5 2.5 2.5 5-5.5" /></>),
    info: (<><circle cx="12" cy="12" r="9" /><path d="M12 11v5" /><circle cx="12" cy="8" r="0.5" fill="currentColor" /></>),
    settings: (<><path d="M4 8h10M18 8h2M4 16h2M10 16h10" /><circle cx="16" cy="8" r="2" /><circle cx="8" cy="16" r="2" /></>),
    statement: (<><path d="M6 2h9l5 5v15H6V2z" /><path d="M14 2v6h6M9 13h7M9 17h7" /></>),
    budget: (<><path d="M12 3v9h9" /><circle cx="12" cy="12" r="9" /></>),
    goal: (<><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" fill="currentColor" /></>),
    card: (<><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></>),
    category: (<><path d="M3 3h8l10 10-8 8L3 11V3z" /><circle cx="8" cy="8" r="1.5" /></>),
};

const EXTRAS: Record<IconExtra, React.ReactNode> = {
    grip: (<path d="M9 6h.01M9 12h.01M9 18h.01M15 6h.01M15 12h.01M15 18h.01" />),
    plus: (<path d="M12 5v14M5 12h14" />),
    check: (<path d="m4 12.5 5 5L20 6.5" />),
    clock: (<><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></>),
    bell: (<path d="M6 9a6 6 0 1 1 12 0c0 5 2 6 2 6H4s2-1 2-6M10 19a2 2 0 0 0 4 0" />),
    lock: (<><rect x="5" y="11" width="14" height="9" rx="2" /><path d="M8 11V8a4 4 0 0 1 8 0v3" /></>),
    send: (<path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />),
    chart: (<path d="M4 20h16M7 16v-4m5 4V8m5 8v-6" />),
};

const TONOS: Record<string, string> = {
    success: "text-[var(--color-success-text)]",
    warning: "text-[var(--color-warning-text)]",
    danger: "text-[var(--color-danger)]",
    info: "text-[var(--color-info-text)]",
    neutral: "text-[var(--color-text-muted)]",
};

export function Icon({ name, tone, className = "", size, title }: IconProps) {
    const paths = (PATHS as Record<string, React.ReactNode>)[name] ?? EXTRAS[name as IconExtra] ?? PATHS.info;
    const dimensionada = typeof size === "number";
    return (
        <svg
            viewBox="0 0 24 24"
            width={dimensionada ? size : undefined}
            height={dimensionada ? size : undefined}
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden={title ? undefined : true}
            role={title ? "img" : undefined}
            aria-label={title}
            focusable="false"
            className={[dimensionada ? "shrink-0" : "h-5 w-5 shrink-0", tone ? TONOS[tone] ?? "" : "", className].join(" ")}
        >
            {paths}
        </svg>
    );
}

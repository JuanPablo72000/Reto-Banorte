"use client";

import type { IconType, Tone } from "@/lib/types/action-plan";

export interface IconProps {
    name: IconType | IconExtra;
    tone?: Tone | null;
    className?: string;
    size?: number;
    title?: string;
}

// Extras internos (grips de reordenado, estados, envíos, shell): NO vienen
// del plan, solo de la UI. Traídos del set de Qwen + navegación.
export type IconExtra =
    | "grip" | "plus" | "check" | "clock" | "bell" | "lock" | "send" | "chart"
    | "home" | "menu" | "close" | "chevron-right" | "chevron-down" | "chevron-up"
    | "user" | "logout" | "accessibility" | "sun" | "moon" | "arrow-up"
    | "refresh" | "eye" | "eye-off" | "filter" | "download" | "grid" | "list"
    | "sparkle" | "wallet" | "piggy" | "shield";

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
    home: (<><path d="m3 11 9-8 9 8" /><path d="M5 10v10h5v-6h4v6h5V10" /></>),
    menu: (<path d="M4 7h16M4 12h16M4 17h16" />),
    close: (<path d="M6 6l12 12M18 6 6 18" />),
    "chevron-right": (<path d="m9 5 7 7-7 7" />),
    "chevron-down": (<path d="m5 9 7 7 7-7" />),
    "chevron-up": (<path d="m5 15 7-7 7 7" />),
    user: (<><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5" /></>),
    logout: (<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="m16 17 5-5-5-5M21 12H9" /></>),
    accessibility: (<><circle cx="12" cy="4.5" r="1.8" /><path d="M4.5 8.5 12 10l7.5-1.5M12 10v5m0 0-3 6m3-6 3 6" /></>),
    sun: (<><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4m11.4-11.4 1.4-1.4" /></>),
    moon: (<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" />),
    "arrow-up": (<path d="M12 20V4m0 0-7 7m7-7 7 7" />),
    refresh: (<><path d="M20 12a8 8 0 1 1-2.3-5.6" /><path d="M20 4v5h-5" /></>),
    eye: (<><path d="M2 12s3.5-6.5 10-6.5S22 12 22 12s-3.5 6.5-10 6.5S2 12 2 12z" /><circle cx="12" cy="12" r="2.8" /></>),
    "eye-off": (<><path d="M4 4l16 16" /><path d="M9.9 5.9A9.9 9.9 0 0 1 12 5.5c6.5 0 10 6.5 10 6.5a17 17 0 0 1-3.2 4.1M6.3 8.1A16.6 16.6 0 0 0 2 12s3.5 6.5 10 6.5c1 0 2-.2 2.8-.5" /><path d="M9.5 10a2.8 2.8 0 0 0 4 4" /></>),
    filter: (<path d="M3 5h18l-7 8v6l-4-2v-4L3 5z" />),
    download: (<><path d="M12 3v12m0 0 5-5m-5 5-5-5" /><path d="M4 21h16" /></>),
    grid: (<><rect x="3" y="3" width="8" height="8" rx="1.5" /><rect x="13" y="3" width="8" height="8" rx="1.5" /><rect x="3" y="13" width="8" height="8" rx="1.5" /><rect x="13" y="13" width="8" height="8" rx="1.5" /></>),
    list: (<path d="M8 6h13M8 12h13M8 18h13M3.5 6h.01M3.5 12h.01M3.5 18h.01" />),
    sparkle: (<><path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3z" /><path d="M19 15.5 20 18l2.5 1-2.5 1-1 2.5-1-2.5L15 19l2.5-1 1-2.5z" /></>),
    wallet: (<><rect x="3" y="6" width="18" height="13" rx="2" /><path d="M3 10h18M16.5 14.5h.01" /></>),
    piggy: (<><path d="M4 12a6 5 0 0 1 6-5h3a6 5 0 0 1 6 5v2h1v3h-2.2A6 5 0 0 1 13 19h-2a6 5 0 0 1-4.8-2.4H4v-3h.3A6 6 0 0 1 4 12z" /><path d="M15.5 11h.01" /></>),
    shield: (<><path d="M12 3 5 6v5.5c0 4.3 2.9 7.7 7 9.5 4.1-1.8 7-5.2 7-9.5V6l-7-3z" /><path d="m9 12 2 2 4-4" /></>),
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

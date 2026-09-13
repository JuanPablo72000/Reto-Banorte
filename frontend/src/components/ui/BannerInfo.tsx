"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import type { IconType, Tone } from "@/lib/types/action-plan";
import { attrsAnimacion } from "@/lib/atributos";

export interface BannerInfoProps {
    title: string;
    description?: string;
    tone?: Tone;
    icon?: IconType;
    animation?: string | null;
    orden?: number;
    autoDismissMs?: number;
    onDismiss?: () => void;
}

const ICONO_POR_TONO: Record<Tone, IconType> = {
    success: "success",
    warning: "warning",
    danger: "warning",
    info: "info",
    neutral: "info",
};

const FONDO_POR_TONO: Record<Tone, string> = {
    success: "bg-[var(--color-success-bg)]",
    warning: "bg-[var(--color-warning-bg)]",
    danger: "bg-[var(--color-danger-bg)]",
    info: "bg-[var(--color-info-bg)]",
    neutral: "bg-[var(--color-surface-2)]",
};

const TEXTO_POR_TONO: Record<Tone, string> = {
    success: "text-[var(--color-success-text)]",
    warning: "text-[var(--color-warning-text)]",
    danger: "text-[var(--color-danger-text)]",
    info: "text-[var(--color-info-text)]",
    neutral: "text-[var(--color-text)]",
};

// Banner de aviso (sección notification del plan): icono + texto según
// tono; role=alert si es crítico, status si no. Auto-cierre pausable.
export function BannerInfo({
    title,
    description,
    tone = "info",
    icon,
    animation = "slide",
    orden = 0,
    autoDismissMs,
    onDismiss,
}: BannerInfoProps) {
    const [pausado, setPausado] = useState(false);
    const attrs = attrsAnimacion(animation, orden);
    const critico = tone === "danger" || tone === "warning";

    useEffect(() => {
        if (!autoDismissMs || autoDismissMs <= 0 || pausado) return;
        const t = window.setTimeout(() => onDismiss?.(), autoDismissMs);
        return () => window.clearTimeout(t);
    }, [autoDismissMs, pausado, onDismiss]);

    return (
        <div
            role={critico ? "alert" : "status"}
            {...attrs}
            onMouseEnter={() => setPausado(true)}
            onMouseLeave={() => setPausado(false)}
            onFocusCapture={() => setPausado(true)}
            onBlurCapture={() => setPausado(false)}
            className={`flex items-start gap-3 rounded-xl border border-[var(--color-border-subtle)] p-[var(--pad-card)] shadow-[var(--shadow-1)] ${FONDO_POR_TONO[tone]}`}
        >
            <span className={`mt-0.5 shrink-0 ${TEXTO_POR_TONO[tone]}`} aria-hidden="true">
                <Icon name={icon ?? ICONO_POR_TONO[tone]} size={20} />
            </span>
            <div className={`flex-1 text-base ${TEXTO_POR_TONO[tone]}`}>
                <p className="font-semibold">{title}</p>
                {description && <p className="mt-0.5 opacity-95">{description}</p>}
            </div>
            {onDismiss && (
                <button
                    type="button"
                    onClick={onDismiss}
                    aria-label={`Cerrar aviso: ${title}`}
                    className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full hover:bg-[var(--color-surface-3)]/60 active:scale-[0.96] motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]"
                >
                    <Icon name="plus" size={18} className="rotate-45" />
                </button>
            )}
        </div>
    );
}

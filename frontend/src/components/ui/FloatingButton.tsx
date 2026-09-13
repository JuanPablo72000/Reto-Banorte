"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";
type Position = "inline" | "bottom-right" | "bottom-left";

export interface FloatingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
    position?: Position;
    icon?: React.ReactNode;
    label: string;
}

const variantClasses: Record<Variant, string> = {
    primary:
        "bg-[var(--color-accent)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)] shadow-[var(--shadow-2)]",
    secondary:
        "bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface-3)] shadow-[var(--shadow-1)]",
    danger: "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)] hover:brightness-95 shadow-[var(--shadow-2)]",
    ghost:
        "bg-[var(--color-surface-2)]/90 backdrop-blur-sm text-[var(--color-text)] hover:bg-[var(--color-surface-3)] shadow-[var(--shadow-1)]",
};

const sizeClasses: Record<Size, string> = {
    sm: "text-sm px-3 py-2 gap-2 min-h-[40px]",
    md: "text-base px-4 py-2.5 gap-2.5 min-h-[48px]",
    lg: "text-lg px-5 py-3 gap-3 min-h-[56px]",
};

// FAB: esquina inferior, nunca a media pantalla tapando contenido;
// en móvil queda arriba del bottom tab bar (bottom offset mayor).
const positionClasses: Record<Position, string> = {
    inline: "",
    "bottom-right":
        "fixed bottom-[calc(var(--bottomnav-h)+1rem)] right-4 z-50 rounded-full lg:bottom-6 lg:right-6",
    "bottom-left":
        "fixed bottom-[calc(var(--bottomnav-h)+1rem)] left-4 z-50 rounded-full lg:bottom-6 lg:left-6",
};

export const FloatingButton = forwardRef<HTMLButtonElement, FloatingButtonProps>(
    (
        {
            variant = "primary",
            size = "md",
            position = "inline",
            icon,
            label,
            disabled,
            className = "",
            ...props
        },
        ref
    ) => {
        const isDisabled = disabled || false;
        const flotante = position !== "inline";

        return (
            <button
                ref={ref}
                type="button"
                disabled={isDisabled}
                aria-busy={false}
                aria-disabled={isDisabled || undefined}
                title={flotante ? label : undefined}
                className={[
                    "inline-flex items-center justify-center font-medium",
                    "transition-[transform,background-color,box-shadow] duration-200 motion-reduce:transition-none",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
                    "focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-[var(--color-surface)]",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    flotante && "ui-fab flex-col p-3.5 hover:scale-105 active:scale-95",
                    variantClasses[variant],
                    sizeClasses[size],
                    positionClasses[position],
                    className,
                ].join(" ")}
                {...props}
            >
                {icon && <span aria-hidden="true">{icon}</span>}
                {flotante ? <span className="sr-only">{label}</span> : <span>{label}</span>}
            </button>
        );
    }
);

FloatingButton.displayName = "FloatingButton";

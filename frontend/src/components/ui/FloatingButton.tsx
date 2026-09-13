"use client";

import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";
type Position = "left" | "right" | "inline";

export interface FloatingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
    position?: Position;
    icon?: React.ReactNode;
    label: string;
}

const variantClasses: Record<Variant, string> = {
    primary:
        "bg-[var(--color-accent)] text-[var(--color-on-accent)] hover:brightness-95 active:brightness-90 shadow-lg",
    secondary:
        "bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface-3)] shadow-md",
    danger: "bg-[var(--color-danger)] text-white hover:brightness-95 shadow-lg",
    ghost:
        "bg-[var(--color-surface-2)]/90 backdrop-blur-sm text-[var(--color-text)] hover:bg-[var(--color-surface-3)] shadow-md",
};

const sizeClasses: Record<Size, string> = {
    sm: "text-sm px-3 py-2 gap-2 min-h-[40px]",
    md: "text-base px-4 py-2.5 gap-2.5 min-h-[48px]",
    lg: "text-lg px-5 py-3 gap-3 min-h-[56px]",
};

const positionClasses: Record<Position, string> = {
    inline: "",
    left: "fixed left-4 top-1/2 -translate-y-1/2 z-50 rounded-full",
    right: "fixed right-4 top-1/2 -translate-y-1/2 z-50 rounded-full",
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

        return (
            <button
                ref={ref}
                disabled={isDisabled}
                aria-busy={false}
                aria-disabled={isDisabled || undefined}
                className={[
                    "inline-flex items-center justify-center font-medium transition-all duration-200",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
                    "focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-[var(--color-bg)]",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "motion-reduce:transition-none",
                    position !== "inline" && "flex-col p-3 hover:scale-105",
                    variantClasses[variant],
                    sizeClasses[size],
                    positionClasses[position],
                    className,
                ].join(" ")}
                {...props}
            >
                {icon && <span aria-hidden="true">{icon}</span>}
                {position === "inline" && <span>{label}</span>}
                {position !== "inline" && (
                    <span className="sr-only">{label}</span>
                )}
            </button>
        );
    }
);

FloatingButton.displayName = "FloatingButton";

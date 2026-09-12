import { ButtonHTMLAttributes, forwardRef } from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: Variant;
    size?: Size;
    loading?: boolean;
}

const variantClasses: Record<Variant, string> = {
    primary:
        "bg-[var(--color-accent)] text-[var(--color-on-accent)] hover:brightness-95 active:brightness-90",
    secondary:
        "bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface-3)]",
    danger: "bg-[var(--color-danger)] text-white hover:brightness-95",
    ghost:
        "bg-transparent text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
};

const sizeClasses: Record<Size, string> = {
    sm: "text-sm px-3 py-1.5 gap-1.5",
    md: "text-base px-4 py-2 gap-2",
    lg: "text-lg px-5 py-3 gap-2.5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            variant = "primary",
            size = "md",
            loading = false,
            disabled,
            className = "",
            children,
            ...props
        },
        ref
    ) => {
        const isDisabled = disabled || loading;

        return (
            <button
                ref={ref}
                disabled={isDisabled}
                aria-busy={loading || undefined}
                aria-disabled={isDisabled || undefined}
                className={[
                    "inline-flex items-center justify-center rounded-md font-medium",
                    "min-h-[44px]",
                    "transition-colors duration-150",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
                    "focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-[var(--color-bg)]",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "motion-reduce:transition-none",
                    variantClasses[variant],
                    sizeClasses[size],
                    className,
                ].join(" ")}
                {...props}
            >
                {loading && (
                    <span
                        aria-hidden="true"
                        className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent motion-reduce:animate-none"
                    />
                )}
                {children}
            </button>
        );
    }
);

Button.displayName = "Button";
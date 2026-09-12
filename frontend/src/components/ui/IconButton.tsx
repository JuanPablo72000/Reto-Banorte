import { ButtonHTMLAttributes, ReactNode, forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    icon: ReactNode;
    "aria-label": string;
    variant?: Variant;
    size?: Size;
}

const variantClasses: Record<Variant, string> = {
    primary: "bg-[var(--color-accent)] text-[var(--color-on-accent)] hover:brightness-95",
    secondary:
        "bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-surface-3)]",
    ghost: "bg-transparent text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
    danger: "bg-transparent text-[var(--color-danger)] hover:bg-[var(--color-danger-bg)]",
};

const sizeClasses: Record<Size, string> = {
    sm: "h-9 w-9",
    md: "h-11 w-11",
    lg: "h-12 w-12",
};

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
    ({ icon, variant = "ghost", size = "md", className = "", ...props }, ref) => {
        return (
            <button
                ref={ref}
                type="button"
                className={[
                    "inline-flex items-center justify-center rounded-full",
                    "transition-colors duration-150 motion-reduce:transition-none",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    variantClasses[variant],
                    sizeClasses[size],
                    className,
                ].join(" ")}
                {...props}
            >
        <span aria-hidden="true" className="flex items-center justify-center">
          {icon}
        </span>
            </button>
        );
    }
);

IconButton.displayName = "IconButton";
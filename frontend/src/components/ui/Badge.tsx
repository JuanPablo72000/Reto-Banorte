import { HTMLAttributes } from "react";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info";

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
    tone?: BadgeTone;
}

const toneClasses: Record<BadgeTone, string> = {
    neutral: "bg-[var(--color-surface-2)] text-[var(--color-text)]",
    success: "bg-[var(--color-success-bg)] text-[var(--color-success-text)]",
    warning: "bg-[var(--color-warning-bg)] text-[var(--color-warning-text)]",
    danger: "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]",
    info: "bg-[var(--color-info-bg)] text-[var(--color-info-text)]",
};

export function Badge({ tone = "neutral", className = "", children, ...props }: BadgeProps) {
    return (
        <span
            className={[
                "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
                toneClasses[tone],
                className,
            ].join(" ")}
            {...props}
        >
      {children}
    </span>
    );
}
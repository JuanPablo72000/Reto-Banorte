import { HTMLAttributes } from "react";

export interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
    value: number;
    max?: number;
    label?: string;
    tone?: "neutral" | "success" | "warning" | "danger";
}

const toneClasses = {
    neutral: "bg-[var(--color-accent)]",
    success: "bg-[var(--color-success-text)]",
    warning: "bg-[var(--color-warning-text)]",
    danger: "bg-[var(--color-danger)]",
};

export function ProgressBar({
                                value,
                                max = 100,
                                label,
                                tone = "neutral",
                                className = "",
                                ...props
                            }: ProgressBarProps) {
    const percentage = Math.min(100, Math.max(0, (value / max) * 100));

    return (
        <div className={["flex flex-col gap-1.5", className].join(" ")} {...props}>
            {label && (
                <div className="flex justify-between text-sm">
                    <span className="text-[var(--color-text)]">{label}</span>
                    <span className="text-[var(--color-text-muted)]">{Math.round(percentage)}%</span>
                </div>
            )}
            <div
                role="progressbar"
                aria-valuenow={value}
                aria-valuemin={0}
                aria-valuemax={max}
                aria-label={label}
                className="h-2 w-full overflow-hidden rounded-full bg-[var(--color-surface-2)]"
            >
                <div
                    className={["h-full rounded-full transition-[width] duration-300 motion-reduce:transition-none", toneClasses[tone]].join(" ")}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}
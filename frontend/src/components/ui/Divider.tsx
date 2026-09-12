import { HTMLAttributes } from "react";

export interface DividerProps extends HTMLAttributes<HTMLDivElement> {
    orientation?: "horizontal" | "vertical";
    label?: string;
}

export function Divider({ orientation = "horizontal", label, className = "", ...props }: DividerProps) {
    if (orientation === "vertical") {
        return (
            <div
                role="separator"
                aria-orientation="vertical"
                className={["w-px self-stretch bg-[var(--color-border)]", className].join(" ")}
                {...props}
            />
        );
    }

    if (label) {
        return (
            <div className={["flex items-center gap-3", className].join(" ")} {...props}>
                <span aria-hidden="true" className="h-px flex-1 bg-[var(--color-border)]" />
                <span className="text-xs font-medium text-[var(--color-text-muted)]">{label}</span>
                <span aria-hidden="true" className="h-px flex-1 bg-[var(--color-border)]" />
            </div>
        );
    }

    return (
        <div
            role="separator"
            aria-orientation="horizontal"
            className={["h-px w-full bg-[var(--color-border)]", className].join(" ")}
            {...props}
        />
    );
}
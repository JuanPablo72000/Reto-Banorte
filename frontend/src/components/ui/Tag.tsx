import { HTMLAttributes, MouseEventHandler } from "react";

export interface TagProps extends HTMLAttributes<HTMLSpanElement> {
    color?: string;
    onRemove?: () => void;
    removeLabel?: string;
}

export function Tag({
                        color,
                        onRemove,
                        removeLabel = "Quitar etiqueta",
                        className = "",
                        children,
                        style,
                        ...props
                    }: TagProps) {
    const handleRemove: MouseEventHandler<HTMLButtonElement> = (e) => {
        e.stopPropagation();
        onRemove?.();
    };

    return (
        <span
            className={[
                "inline-flex items-center gap-1.5 rounded-md border border-[var(--color-border)]",
                "bg-[var(--color-surface-2)] px-2 py-1 text-sm text-[var(--color-text)]",
                className,
            ].join(" ")}
            style={{ borderLeftColor: color, borderLeftWidth: color ? 3 : undefined, ...style }}
            {...props}
        >
      {children}
            {onRemove && (
                <button
                    type="button"
                    onClick={handleRemove}
                    aria-label={removeLabel}
                    className={[
                        "rounded-sm leading-none text-[var(--color-text-muted)]",
                        "hover:text-[var(--color-danger)]",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                    ].join(" ")}
                >
                    <span aria-hidden="true">×</span>
                </button>
            )}
    </span>
    );
}
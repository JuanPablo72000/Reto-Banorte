import { InputHTMLAttributes, forwardRef, useId } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label: string;
    error?: string;
    hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, error, hint, id, className = "", ...props }, ref) => {
        const generatedId = useId();
        const inputId = id ?? generatedId;
        const hintId = hint ? `${inputId}-hint` : undefined;
        const errorId = error ? `${inputId}-error` : undefined;

        return (
            <div className="flex flex-col gap-1.5">
                <label htmlFor={inputId} className="text-sm font-medium text-[var(--color-text)]">
                    {label}
                </label>

                {hint && (
                    <span id={hintId} className="text-sm text-[var(--color-text-muted)]">
            {hint}
          </span>
                )}

                <input
                    ref={ref}
                    id={inputId}
                    aria-invalid={!!error || undefined}
                    aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
                    className={[
                        "min-h-[44px] rounded-md border bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]",
                        "placeholder:text-[var(--color-text-muted)]",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                        error ? "border-[var(--color-danger)]" : "border-[var(--color-border)]",
                        "disabled:opacity-50 disabled:cursor-not-allowed",
                        className,
                    ].join(" ")}
                    {...props}
                />

                {error && (
                    <span id={errorId} role="alert" className="text-sm text-[var(--color-danger)]">
            {error}
          </span>
                )}
            </div>
        );
    }
);

Input.displayName = "Input";
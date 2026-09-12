import { TextareaHTMLAttributes, forwardRef, useId } from "react";

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
    label: string;
    error?: string;
    hint?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
    ({ label, error, hint, id, className = "", rows = 3, ...props }, ref) => {
        const generatedId = useId();
        const textareaId = id ?? generatedId;
        const hintId = hint ? `${textareaId}-hint` : undefined;
        const errorId = error ? `${textareaId}-error` : undefined;

        return (
            <div className="flex flex-col gap-1.5">
                <label htmlFor={textareaId} className="text-sm font-medium text-[var(--color-text)]">
                    {label}
                </label>

                {hint && (
                    <span id={hintId} className="text-sm text-[var(--color-text-muted)]">
            {hint}
          </span>
                )}

                <textarea
                    ref={ref}
                    id={textareaId}
                    rows={rows}
                    aria-invalid={!!error || undefined}
                    aria-describedby={[hintId, errorId].filter(Boolean).join(" ") || undefined}
                    className={[
                        "rounded-md border bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]",
                        "placeholder:text-[var(--color-text-muted)] resize-y",
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

Textarea.displayName = "Textarea";
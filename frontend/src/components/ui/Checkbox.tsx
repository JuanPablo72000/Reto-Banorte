import { InputHTMLAttributes, forwardRef, useId } from "react";

export interface CheckboxProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type"> {
    label: string;
    hint?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
    ({ label, hint, id, className = "", ...props }, ref) => {
        const generatedId = useId();
        const checkboxId = id ?? generatedId;
        const hintId = hint ? `${checkboxId}-hint` : undefined;

        return (
            <div className="flex items-start gap-2.5">
                <input
                    ref={ref}
                    type="checkbox"
                    id={checkboxId}
                    aria-describedby={hintId}
                    className={[
                        "mt-0.5 h-5 w-5 shrink-0 rounded border-[var(--color-border)]",
                        "accent-[var(--color-accent)]",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                        "disabled:opacity-50 disabled:cursor-not-allowed",
                        className,
                    ].join(" ")}
                    {...props}
                />
                <div className="flex flex-col">
                    <label htmlFor={checkboxId} className="text-sm font-medium text-[var(--color-text)] cursor-pointer">
                        {label}
                    </label>
                    {hint && (
                        <span id={hintId} className="text-sm text-[var(--color-text-muted)]">
              {hint}
            </span>
                    )}
                </div>
            </div>
        );
    }
);

Checkbox.displayName = "Checkbox";
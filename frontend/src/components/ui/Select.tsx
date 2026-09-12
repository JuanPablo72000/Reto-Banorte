import { SelectHTMLAttributes, forwardRef, useId } from "react";

export interface SelectOption {
    value: string;
    label: string;
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
    label: string;
    options: SelectOption[];
    error?: string;
    placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
    ({ label, options, error, placeholder, id, className = "", ...props }, ref) => {
        const generatedId = useId();
        const selectId = id ?? generatedId;
        const errorId = error ? `${selectId}-error` : undefined;

        return (
            <div className="flex flex-col gap-1.5">
                <label htmlFor={selectId} className="text-sm font-medium text-[var(--color-text)]">
                    {label}
                </label>

                <select
                    ref={ref}
                    id={selectId}
                    aria-invalid={!!error || undefined}
                    aria-describedby={errorId}
                    defaultValue={props.defaultValue ?? ""}
                    className={[
                        "min-h-[44px] rounded-md border bg-[var(--color-surface)] px-3 py-2 text-[var(--color-text)]",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                        error ? "border-[var(--color-danger)]" : "border-[var(--color-border)]",
                        "disabled:opacity-50 disabled:cursor-not-allowed",
                        className,
                    ].join(" ")}
                    {...props}
                >
                    {placeholder && (
                        <option value="" disabled>
                            {placeholder}
                        </option>
                    )}
                    {options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>

                {error && (
                    <span id={errorId} role="alert" className="text-sm text-[var(--color-danger)]">
            {error}
          </span>
                )}
            </div>
        );
    }
);

Select.displayName = "Select";
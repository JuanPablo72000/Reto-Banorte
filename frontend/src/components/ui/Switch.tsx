import { ButtonHTMLAttributes, forwardRef, useId } from "react";

export interface SwitchProps
    extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "onChange" | "value"> {
    label: string;
    checked: boolean;
    onCheckedChange: (checked: boolean) => void;
    hint?: string;
}

export const Switch = forwardRef<HTMLButtonElement, SwitchProps>(
    ({ label, checked, onCheckedChange, hint, id, className = "", ...props }, ref) => {
        const generatedId = useId();
        const switchId = id ?? generatedId;
        const hintId = hint ? `${switchId}-hint` : undefined;

        return (
            <div className="flex items-center justify-between gap-4">
                <div className="flex flex-col">
          <span id={`${switchId}-label`} className="text-sm font-medium text-[var(--color-text)]">
            {label}
          </span>
                    {hint && (
                        <span id={hintId} className="text-sm text-[var(--color-text-muted)]">
              {hint}
            </span>
                    )}
                </div>

                <button
                    ref={ref}
                    id={switchId}
                    type="button"
                    role="switch"
                    aria-checked={checked}
                    aria-labelledby={`${switchId}-label`}
                    aria-describedby={hintId}
                    onClick={() => onCheckedChange(!checked)}
                    className={[
                        "relative inline-flex h-7 w-12 shrink-0 items-center rounded-full transition-colors",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2",
                        "motion-reduce:transition-none",
                        checked ? "bg-[var(--color-accent)]" : "bg-[var(--color-surface-3)]",
                        className,
                    ].join(" ")}
                    {...props}
                >
          <span
              aria-hidden="true"
              className={[
                  "inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform",
                  "motion-reduce:transition-none",
                  checked ? "translate-x-6" : "translate-x-1",
              ].join(" ")}
          />
                </button>
            </div>
        );
    }
);

Switch.displayName = "Switch";
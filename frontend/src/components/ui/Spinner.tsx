import { HTMLAttributes } from "react";

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
    size?: "sm" | "md" | "lg";
    label?: string;
}

const sizeClasses = {
    sm: "h-4 w-4 border-2",
    md: "h-6 w-6 border-2",
    lg: "h-10 w-10 border-[3px]",
};

export function Spinner({ size = "md", label = "Cargando", className = "", ...props }: SpinnerProps) {
    return (
        <div role="status" className={["inline-flex items-center gap-2", className].join(" ")} {...props}>
      <span
          aria-hidden="true"
          className={[
              "animate-spin rounded-full border-current border-t-transparent text-[var(--color-accent)]",
              "motion-reduce:animate-none",
              sizeClasses[size],
          ].join(" ")}
      />
            <span className="sr-only">{label}</span>
        </div>
    );
}
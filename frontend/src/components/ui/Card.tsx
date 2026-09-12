import { HTMLAttributes, forwardRef } from "react";

export type CardProps = HTMLAttributes<HTMLDivElement>;

export const Card = forwardRef<HTMLDivElement, CardProps>(
    ({ className = "", children, ...props }, ref) => {
        return (
            <div
                ref={ref}
                className={[
                    "rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]",
                    "p-4",
                    className,
                ].join(" ")}
                {...props}
            >
                {children}
            </div>
        );
    }
);

Card.displayName = "Card";

export const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
    ({ className = "", children, ...props }, ref) => (
        <div ref={ref} className={["mb-3 flex items-center justify-between gap-2", className].join(" ")} {...props}>
            {children}
        </div>
    )
);
CardHeader.displayName = "CardHeader";

export const CardTitle = forwardRef<HTMLHeadingElement, HTMLAttributes<HTMLHeadingElement>>(
    ({ className = "", children, ...props }, ref) => (
        <h3 ref={ref} className={["text-base font-semibold text-[var(--color-text)]", className].join(" ")} {...props}>
            {children}
        </h3>
    )
);
CardTitle.displayName = "CardTitle";
import { HTMLAttributes } from "react";

export type SkeletonProps = HTMLAttributes<HTMLDivElement>;

export function Skeleton({ className = "", ...props }: SkeletonProps) {
    return (
        <div
            aria-hidden="true"
            className={[
                "animate-pulse rounded-md bg-[var(--color-surface-2)]",
                "motion-reduce:animate-none",
                className,
            ].join(" ")}
            {...props}
        />
    );
}
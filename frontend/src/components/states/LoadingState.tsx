import { Spinner } from "../ui/Spinner";
import { Skeleton } from "../ui/Skeleton";

export interface LoadingStateProps {
    message?: string;
    variant?: "spinner" | "skeleton";
    skeletonRows?: number;
}

export function LoadingState({ message = "Cargando", variant = "spinner", skeletonRows = 3 }: LoadingStateProps) {
    if (variant === "skeleton") {
        return (
            <div role="status" aria-label={message} className="flex flex-col gap-3 p-4">
                {Array.from({ length: skeletonRows }).map((_, i) => (
                    <Skeleton key={i} className="h-14 w-full" />
                ))}
                <span className="sr-only">{message}</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center gap-3 p-10 text-center">
            <Spinner size="lg" label={message} />
            <p className="text-sm text-[var(--color-text-muted)]">{message}</p>
        </div>
    );
}
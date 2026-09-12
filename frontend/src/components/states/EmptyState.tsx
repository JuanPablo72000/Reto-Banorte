import { ReactNode } from "react";
import { Button } from "../ui/Button";

export interface EmptyStateProps {
    title: string;
    description?: string;
    icon?: ReactNode;
    actionLabel?: string;
    onAction?: () => void;
}

export function EmptyState({ title, description, icon, actionLabel, onAction }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center gap-3 p-10 text-center">
            {icon && (
                <div aria-hidden="true" className="text-[var(--color-text-muted)]">
                    {icon}
                </div>
            )}
            <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
            {description && (
                <p className="max-w-sm text-sm text-[var(--color-text-muted)]">{description}</p>
            )}
            {actionLabel && onAction && (
                <Button variant="primary" size="sm" onClick={onAction} className="mt-2">
                    {actionLabel}
                </Button>
            )}
        </div>
    );
}
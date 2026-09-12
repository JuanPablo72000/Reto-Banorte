import { Button } from "../ui/Button";

export interface ErrorStateProps {
    title?: string;
    description?: string;
    retryLabel?: string;
    onRetry?: () => void;
}

export function ErrorState({
                               title = "No se pudo cargar la información",
                               description = "Ocurrió un problema al conectar con el servidor. Intenta de nuevo.",
                               retryLabel = "Reintentar",
                               onRetry,
                           }: ErrorStateProps) {
    return (
        <div
            role="alert"
            className="flex flex-col items-center justify-center gap-3 rounded-lg border border-[var(--color-danger-bg)] bg-[var(--color-danger-bg)]/40 p-10 text-center"
        >
      <span aria-hidden="true" className="text-2xl text-[var(--color-danger)]">
        ⚠
      </span>
            <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
            <p className="max-w-sm text-sm text-[var(--color-text-muted)]">{description}</p>
            {onRetry && (
                <Button variant="secondary" size="sm" onClick={onRetry} className="mt-2">
                    {retryLabel}
                </Button>
            )}
        </div>
    );
}
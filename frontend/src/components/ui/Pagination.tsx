export interface PaginationProps {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
    if (totalPages <= 1) return null;

    const canGoPrev = currentPage > 1;
    const canGoNext = currentPage < totalPages;

    const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

    return (
        <nav aria-label="Paginación" className="flex items-center justify-center gap-1">
            <button
                type="button"
                onClick={() => onPageChange(currentPage - 1)}
                disabled={!canGoPrev}
                aria-label="Página anterior"
                className={[
                    "min-h-[40px] min-w-[40px] rounded-md text-sm font-medium",
                    "text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                    "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                ].join(" ")}
            >
                ‹
            </button>

            {pages.map((page) => {
                const isCurrent = page === currentPage;
                return (
                    <button
                        key={page}
                        type="button"
                        onClick={() => onPageChange(page)}
                        aria-current={isCurrent ? "page" : undefined}
                        aria-label={`Página ${page}`}
                        className={[
                            "min-h-[40px] min-w-[40px] rounded-md text-sm font-medium",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                            isCurrent
                                ? "bg-[var(--color-accent)] text-[var(--color-on-accent)]"
                                : "text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                        ].join(" ")}
                    >
                        {page}
                    </button>
                );
            })}

            <button
                type="button"
                onClick={() => onPageChange(currentPage + 1)}
                disabled={!canGoNext}
                aria-label="Página siguiente"
                className={[
                    "min-h-[40px] min-w-[40px] rounded-md text-sm font-medium",
                    "text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                    "disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                ].join(" ")}
            >
                ›
            </button>
        </nav>
    );
}
"use client";

import { Skeleton } from "@/components/ui/Skeleton";

// Pantalla de carga con diseño: imita la forma de la respuesta (mensaje +
// tarjeta + botones) mientras /api/chat genera el plan. Usa el primitivo
// Skeleton (respeta reduced-motion) y role="status" para lectores.
export function ChatSkeleton() {
    return (
        <div className="flex w-full flex-col gap-4" role="status" aria-label="Generando respuesta">
            <Skeleton className="h-6 w-3/4" />
            <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                <Skeleton className="h-8 w-1/2" />
                <div className="mt-4 flex flex-col gap-2">
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-full" />
                    <Skeleton className="h-10 w-2/3" />
                </div>
            </div>
            <div className="flex flex-wrap gap-2">
                <Skeleton className="h-11 w-40" />
                <Skeleton className="h-11 w-48" />
            </div>
            <span className="sr-only">Generando tu respuesta…</span>
        </div>
    );
}

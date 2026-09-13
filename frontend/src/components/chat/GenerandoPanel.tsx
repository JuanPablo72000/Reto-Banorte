"use client";

// Pantalla de carga CON movimiento mientras /api/chat genera el plan:
// logo con anillos pulsantes y brillo, barra indeterminada, mensajes de
// progreso rotativos y skeletons shimmer. Reemplaza a ChatSkeleton.
// role="status" para lectores; el CSS global apaga todo con reduced-motion.

import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Skeleton";

const PASOS = [
    "Pensando en tu solicitud…",
    "Consultando tus datos…",
    "Eligiendo la mejor visualización…",
    "Generando tu interfaz…",
];

const PASO_MS = 2200;

export function GenerandoPanel({ etiqueta = "Generando tu respuesta" }: { etiqueta?: string }) {
    const [paso, setPaso] = useState(0);

    useEffect(() => {
        const t = setInterval(() => setPaso((p) => (p + 1) % PASOS.length), PASO_MS);
        return () => clearInterval(t);
    }, []);

    return (
        <div className="flex w-full flex-col gap-6" role="status" aria-label={etiqueta}>
            <span className="sr-only" aria-live="polite">
                {PASOS[paso]}
            </span>

            {/* Logo animado: anillos pulsantes + órbita + brillo */}
            <div className="flex flex-col items-center gap-5 py-6">
                <div className="relative flex h-20 w-20 items-center justify-center">
                    <span className="ring-pulse absolute inset-0" aria-hidden="true" />
                    <span className="ui-spin absolute inset-0 rounded-full border-2 border-dashed border-[var(--color-accent)] opacity-60 motion-reduce:animate-none" aria-hidden="true" />
                    <span className="logo-shine relative flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-[var(--shadow-2)]">
                        <Icon name="sparkle" size={24} />
                    </span>
                </div>

                <div className="flex w-full max-w-sm flex-col gap-3">
                    <p
                        key={paso}
                        aria-hidden="true"
                        className="ui-pop text-center text-sm font-medium text-[var(--color-text)]"
                    >
                        {PASOS[paso]}
                    </p>
                    <div className="progress-indeterminate" aria-hidden="true" />
                </div>
            </div>

            {/* Skeleton de la respuesta por venir */}
            <div className="flex flex-col gap-4">
                <Skeleton className="h-5 w-2/3" />
                <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
                    <Skeleton className="h-7 w-1/2" />
                    <div className="mt-4 flex flex-col gap-2.5">
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-full" />
                        <Skeleton className="h-10 w-4/5" />
                    </div>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Skeleton className="h-11 w-36 rounded-full" />
                    <Skeleton className="h-11 w-44 rounded-full" />
                </div>
            </div>
        </div>
    );
}

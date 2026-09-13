"use client";

import type { ReactNode } from "react";
import type { ExecutedStep } from "@/lib/types/action-plan";
import type { Seccion, VistaEnVivo } from "@/lib/layout";

// Layout por x_position: cada sección del plan va a su slot.
// Responsive: header/footer a lo ancho; main+sidebar lado a lado en lg y
// apilados en móvil; modal/inline/notification como bloques contextuales.
// data-density y data-vista los gobierna ViewControls (ver globals.css).
export function PlanLayout({
    grupos,
    renderStep,
    vista,
}: {
    grupos: Record<Seccion, ExecutedStep[]>;
    renderStep: (step: ExecutedStep, indice: number) => ReactNode;
    vista: VistaEnVivo;
}) {
    const densidad = vista.tamano === "sm" ? "compacto" : vista.tamano === "lg" ? "amplio" : "normal";
    const vistaTabla = vista.vista === "auto" ? undefined : vista.vista;

    return (
        <div
            className="flex w-full flex-col gap-[var(--plan-gap)]"
            data-density={densidad}
            {...(vistaTabla ? { "data-vista": vistaTabla } : {})}
        >
            {grupos.header.length > 0 && (
                <header className="flex w-full flex-col gap-[var(--plan-gap)]">
                    {grupos.header.map(renderStep)}
                </header>
            )}

            <div className="grid w-full grid-cols-1 gap-[var(--plan-gap)] lg:grid-cols-3">
                <div className="flex flex-col gap-[var(--plan-gap)] lg:col-span-2">
                    {grupos.main.map(renderStep)}
                    {grupos.inline.map(renderStep)}
                </div>
                {grupos.sidebar.length > 0 && (
                    <aside
                        aria-label="Información complementaria"
                        className="flex flex-col gap-[var(--plan-gap)]"
                    >
                        {grupos.sidebar.map(renderStep)}
                    </aside>
                )}
            </div>

            {grupos.notification.length > 0 && (
                <div role="status" className="flex w-full flex-col gap-[var(--plan-gap)]">
                    {grupos.notification.map(renderStep)}
                </div>
            )}

            {grupos.footer.length > 0 && (
                <footer className="flex w-full flex-col gap-[var(--plan-gap)] text-sm text-[var(--color-text-muted)]">
                    {grupos.footer.map(renderStep)}
                </footer>
            )}

            {grupos.modal.length > 0 && (
                <div className="flex w-full flex-col gap-[var(--plan-gap)]">
                    {grupos.modal.map(renderStep)}
                </div>
            )}
        </div>
    );
}

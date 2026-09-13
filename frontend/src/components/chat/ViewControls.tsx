"use client";

import { Button } from "@/components/ui/Button";
import { useA11y } from "@/components/accessibility/A11yProvider";
import { type VistaEnVivo } from "@/lib/layout";

function Grupo<T extends string>({
    etiqueta,
    opciones,
    valor,
    onElegir,
}: {
    etiqueta: string;
    opciones: { valor: T; texto: string }[];
    valor: T;
    onElegir: (v: T) => void;
}) {
    return (
        <div className="flex items-center gap-1" role="group" aria-label={etiqueta}>
            <span className="text-xs text-[var(--color-text-muted)]">{etiqueta}:</span>
            {opciones.map((o) => (
                <Button
                    key={o.valor}
                    variant={valor === o.valor ? "primary" : "ghost"}
                    size="sm"
                    onClick={() => onElegir(o.valor)}
                    aria-pressed={valor === o.valor}
                >
                    {o.texto}
                </Button>
            ))}
        </div>
    );
}

// Ajuste en vivo del plan SIN llamar a la IA: tamaño, vista y contraste.
// Controlado por el padre (PlanRenderer es dueño del estado vía
// useVistaEnVivo); el override local gana a la plantilla de la IA.
export function ViewControls({
    vista,
    onChange,
}: {
    vista: VistaEnVivo;
    onChange: (v: VistaEnVivo) => void;
}) {
    const a11y = useA11y();

    function cambiar(parche: Partial<VistaEnVivo>) {
        const next = { ...vista, ...parche };
        onChange(next);
        if (parche.contraste) {
            if (parche.contraste === "auto") {
                // Vuelve a contraste normal; el próximo plan reaplica plantilla.
                a11y.setContrast("normal");
            } else {
                a11y.setContrast(parche.contraste === "high" ? "high" : "normal");
            }
        }
    }

    return (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-2">
            <Grupo
                etiqueta="Tamaño"
                valor={vista.tamano}
                onElegir={(v) => cambiar({ tamano: v })}
                opciones={[
                    { valor: "auto", texto: "Auto" },
                    { valor: "sm", texto: "S" },
                    { valor: "md", texto: "M" },
                    { valor: "lg", texto: "L" },
                ]}
            />
            <Grupo
                etiqueta="Vista"
                valor={vista.vista}
                onElegir={(v) => cambiar({ vista: v })}
                opciones={[
                    { valor: "auto", texto: "Auto" },
                    { valor: "tabla", texto: "Tabla" },
                    { valor: "tarjetas", texto: "Tarjetas" },
                ]}
            />
            <Grupo
                etiqueta="Contraste"
                valor={vista.contraste}
                onElegir={(v) => cambiar({ contraste: v })}
                opciones={[
                    { valor: "auto", texto: "Auto" },
                    { valor: "normal", texto: "Normal" },
                    { valor: "high", texto: "Alto" },
                ]}
            />
        </div>
    );
}

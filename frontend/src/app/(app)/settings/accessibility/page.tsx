"use client";

// Página de accesibilidad: los mismos controles del panel lateral, en
// formato de página completa (alternativa sin drawer).

import { ControlesAccesibilidad } from "@/components/accessibility/AccessibilityPanel";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";

export default function AccessibilitySettingsPage() {
    return (
        <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)]">
                    <Icon name="accessibility" size={22} />
                </span>
                <div>
                    <h2 className="text-xl font-semibold text-[var(--color-text)]">Accesibilidad</h2>
                    <p className="text-sm text-[var(--color-text-muted)]">
                        Ajusta la interfaz a tus necesidades. Los cambios se aplican al instante y se guardan en este dispositivo.
                    </p>
                </div>
            </header>

            <Card className="ui-rise p-0" style={{ "--orden": 1 } as React.CSSProperties}>
                <ControlesAccesibilidad />
            </Card>
        </div>
    );
}

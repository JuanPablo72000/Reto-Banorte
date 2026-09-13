"use client";

import { Card } from "@/components/ui/Card";
import { CompactRow } from "@/components/ui/CompactRow";
import type { ExecutedStep } from "@/lib/types/action-plan";
import { campo, objeto } from "@/lib/plan-result";

// get_user_context (none) — perfil + accesibilidad en filas densas.
export function UserContextCard({ step }: { step: ExecutedStep }) {
    const u = objeto<Record<string, unknown>>(step.result);
    if (!u) return <p className="text-sm">Sin datos del usuario.</p>;
    const acc = (u.accessibility ?? {}) as Record<string, unknown>;
    return (
        <Card>
            <p className="font-medium text-[var(--color-text)]">{campo<string>(u, "name", "—")}</p>
            <p className="text-sm text-[var(--color-text-muted)]">{campo<string>(u, "email", "—")}</p>
            <ul className="mt-2">
                <CompactRow
                    label="Perfil de accesibilidad"
                    value={campo<string>(acc, "accessibility_profile", "default")}
                    icon="account"
                />
                <CompactRow
                    label="Idioma"
                    value={campo<string>(u, "locale", "es-MX")}
                    icon="info"
                />
            </ul>
        </Card>
    );
}

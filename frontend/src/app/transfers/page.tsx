"use client";

import { useState } from "react";
import { ErrorState } from "@/components/states/ErrorState";
import { ChatSkeleton } from "@/components/chat/ChatSkeleton";
import { PlanRenderer } from "@/components/chat/PlanRenderer";
import { TransferManualForm } from "@/components/transfers/TransferManualForm";
import type { ActionPlanUI, SuggestedAction } from "@/lib/types/action-plan";

// Ruta /transfers: formulario manual por pasos que compone el mensaje y
// lo manda por el flujo normal del chat (IA -> confirmación -> ejecución).
export default function TransfersPage() {
    const [plan, setPlan] = useState<ActionPlanUI | null>(null);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [ultimoMensaje, setUltimoMensaje] = useState("");

    async function enviar(mensaje: string, confirmado = false) {
        setCargando(true);
        setError(null);
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    mensaje,
                    contexto: { id_user: 1, id_account: 1, confirmado },
                }),
            });
            const data = (await res.json()) as ActionPlanUI;
            if (!res.ok || data.error) {
                setError(data.error ?? `error ${res.status}`);
                return;
            }
            setPlan(data);
            setUltimoMensaje(mensaje);
        } catch (e) {
            setError(e instanceof Error ? e.message : "error de red");
        } finally {
            setCargando(false);
        }
    }

    return (
        <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 p-6">
            <h1 className="text-2xl font-semibold text-[var(--color-text)]">Transferencias</h1>
            {!plan && !cargando && !error && <TransferManualForm onListo={(m) => void enviar(m)} />}
            {cargando && <ChatSkeleton />}
            {error && (
                <ErrorState description={error} onRetry={() => ultimoMensaje && void enviar(ultimoMensaje)} />
            )}
            {plan && !cargando && !error && (
                <>
                    <PlanRenderer
                        plan={plan}
                        onSugerencia={(a: SuggestedAction) => void enviar(a.label)}
                        onConfirmar={() => void enviar(ultimoMensaje, true)}
                    />
                    <button
                        type="button"
                        onClick={() => setPlan(null)}
                        className="self-start text-sm text-[var(--color-text-muted)] underline"
                    >
                        Hacer otra transferencia
                    </button>
                </>
            )}
        </div>
    );
}

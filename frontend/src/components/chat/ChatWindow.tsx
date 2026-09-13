"use client";

import { useState } from "react";
import { ErrorState } from "@/components/states/ErrorState";
import { ChatComposer } from "./ChatComposer";
import { ChatSkeleton } from "./ChatSkeleton";
import { PlanRenderer } from "./PlanRenderer";
import type { ActionPlanUI, ChatContext, SuggestedAction } from "@/lib/types/action-plan";
import { WELCOME_TEXT } from "./types";

const CONTEXTO_BASE: ChatContext = { id_user: 1, id_account: 1 };

export function ChatWindow() {
    const [plan, setPlan] = useState<ActionPlanUI | null>(null);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [ultimoMensaje, setUltimoMensaje] = useState("");

    async function enviar(mensaje: string, contexto: ChatContext = CONTEXTO_BASE) {
        setCargando(true);
        setError(null);
        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mensaje, contexto }),
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

    function handleSugerencia(a: SuggestedAction) {
        if (cargando) return;
        void enviar(a.label);
    }

    function handleConfirmar() {
        if (!ultimoMensaje || cargando) return;
        void enviar(ultimoMensaje, { ...CONTEXTO_BASE, confirmado: true });
    }

    return (
        <div className="flex h-full flex-col items-center justify-between p-6">
            <div className="flex w-full max-w-2xl flex-1 flex-col items-center gap-6 overflow-y-auto">
                {!plan && !cargando && !error && (
                    <h1 className="text-center text-3xl font-semibold text-[var(--color-text)] sm:text-4xl">
                        {WELCOME_TEXT}
                    </h1>
                )}
                {cargando && <ChatSkeleton />}
                {error && <ErrorState description={error} onRetry={() => ultimoMensaje && void enviar(ultimoMensaje)} />}
                {plan && !cargando && !error && (
                    <PlanRenderer plan={plan} onSugerencia={handleSugerencia} onConfirmar={handleConfirmar} />
                )}
            </div>

            <div className="w-full max-w-2xl border-t border-[var(--color-border)] pt-4">
                <ChatComposer onSend={(texto) => enviar(texto)} sending={cargando} />
            </div>
        </div>
    );
}

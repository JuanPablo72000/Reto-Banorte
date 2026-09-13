"use client";

import { useState } from "react";
import { ErrorState } from "@/components/states/ErrorState";
import { ChatComposer } from "./ChatComposer";
import { ChatSkeleton } from "./ChatSkeleton";
import { PlanRenderer } from "./PlanRenderer";
import { FloatingButton } from "@/components/ui/FloatingButton";
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
        // Se manda el tool/arguments exactos junto con el texto, para que
        // el botón funcione siempre (ver accion_directa en orquestador.py)
        // y no dependa de que la IA adivine bien el texto del botón.
        void enviar(a.label, {
            ...CONTEXTO_BASE,
            accion_directa: { tool: a.tool, arguments: a.arguments, label: a.label },
        });
    }

    function handleConfirmar() {
        if (!ultimoMensaje || cargando) return;
        void enviar(ultimoMensaje, { ...CONTEXTO_BASE, confirmado: true });
    }

    function handleScrollToTop() {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    function handleNuevaConsulta() {
        setPlan(null);
        setUltimoMensaje("");
        setError(null);
    }

    return (
        <div className="flex h-full flex-col items-center justify-between p-6">
            {/* Botón flotante izquierdo - Nueva consulta */}
            <FloatingButton
                position="left"
                variant="secondary"
                size="md"
                label="Nueva consulta"
                onClick={handleNuevaConsulta}
                icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                }
                aria-label="Iniciar nueva consulta"
            />

            {/* Botón flotante derecho - Ir arriba */}
            <FloatingButton
                position="right"
                variant="primary"
                size="md"
                label="Ir arriba"
                onClick={handleScrollToTop}
                icon={
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
                    </svg>
                }
                aria-label="Volver al inicio"
            />

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

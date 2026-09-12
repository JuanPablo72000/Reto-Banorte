"use client";

import { useState, FormEvent } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { LoadingState } from "@/components/states/LoadingState";
import { ErrorState } from "@/components/states/ErrorState";
import { PlanRenderer } from "./PlanRenderer";
import type { ActionPlanUI, ChatContext, SuggestedAction } from "@/lib/types/action-plan";
import { WELCOME_TEXT } from "./types";

const CONTEXTO_BASE: ChatContext = { id_user: 1, id_account: 1 };

export function ChatWindow() {
    const [plan, setPlan] = useState<ActionPlanUI | null>(null);
    const [draft, setDraft] = useState("");
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

    function handleSend(e: FormEvent) {
        e.preventDefault();
        if (!draft.trim() || cargando) return;
        void enviar(draft.trim());
        setDraft("");
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
                {cargando && <LoadingState />}
                {error && <ErrorState description={error} onRetry={() => ultimoMensaje && void enviar(ultimoMensaje)} />}
                {plan && !cargando && !error && (
                    <PlanRenderer plan={plan} onSugerencia={handleSugerencia} onConfirmar={handleConfirmar} />
                )}
            </div>

            <form
                onSubmit={handleSend}
                className="flex w-full max-w-2xl items-end gap-2 border-t border-[var(--color-border)] pt-4"
            >
                <div className="flex-1">
                    <Input
                        label="Mensaje"
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        placeholder="Escribe tu mensaje..."
                    />
                </div>
                <Button type="submit">Enviar</Button>
            </form>
        </div>
    );
}

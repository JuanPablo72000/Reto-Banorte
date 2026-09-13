"use client";

// Lógica del chat extraída de ChatWindow para reutilizarla en el home
// (2 paneles) y en las páginas con bloques "Preguntar a Cain".
// El contrato con /api/chat no cambia.

import { useCallback, useState } from "react";
import { useAuth } from "@/components/auth/AuthProvider";
import type { ActionPlanUI, ChatContext, SuggestedAction } from "@/lib/types/action-plan";

export interface MensajeHilo {
    rol: "user" | "assistant";
    texto: string;
}

export function useChatPlan() {
    const { session } = useAuth();
    const [plan, setPlan] = useState<ActionPlanUI | null>(null);
    const [cargando, setCargando] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [ultimoMensaje, setUltimoMensaje] = useState("");
    const [hilo, setHilo] = useState<MensajeHilo[]>([]);

    const contextoBase = useCallback((): ChatContext => {
        const ctx: ChatContext = { id_user: session?.user.id ?? 1, id_account: 1 };
        if (session?.token) ctx.token = session.token;
        return ctx;
    }, [session]);

    const enviar = useCallback(
        async (mensaje: string, extra?: Partial<ChatContext>) => {
            setCargando(true);
            setError(null);
            try {
                const res = await fetch("/api/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mensaje, contexto: { ...contextoBase(), ...extra } }),
                });
                const data = (await res.json()) as ActionPlanUI;
                if (!res.ok || data.error) {
                    setError(data.error ?? `error ${res.status}`);
                    return;
                }
                setPlan(data);
                setUltimoMensaje(mensaje);
                setHilo((prev) => [
                    ...prev,
                    { rol: "user", texto: mensaje },
                    {
                        rol: "assistant",
                        texto:
                            data.accessibility_template !== "default" && data.response_to_user_plain_language
                                ? data.response_to_user_plain_language
                                : data.response_to_user,
                    },
                ]);
            } catch (e) {
                setError(e instanceof Error ? e.message : "error de red");
            } finally {
                setCargando(false);
            }
        },
        [contextoBase],
    );

    // Botón de sugerencia: se mandan tool/arguments exactos (accion_directa)
    // para que el paso se ejecute garantizado, sin depender de la IA.
    const enviarSugerencia = useCallback(
        (a: SuggestedAction) => {
            if (cargando) return;
            void enviar(a.label, {
                accion_directa: { tool: a.tool, arguments: a.arguments, label: a.label },
            });
        },
        [cargando, enviar],
    );

    const confirmar = useCallback(() => {
        if (!ultimoMensaje || cargando) return;
        void enviar(ultimoMensaje, { confirmado: true });
    }, [ultimoMensaje, cargando, enviar]);

    const reintentar = useCallback(() => {
        if (ultimoMensaje) void enviar(ultimoMensaje);
    }, [ultimoMensaje, enviar]);

    const nuevaConsulta = useCallback(() => {
        setPlan(null);
        setUltimoMensaje("");
        setError(null);
        setHilo([]);
    }, []);

    return {
        plan,
        cargando,
        error,
        ultimoMensaje,
        hilo,
        enviar,
        enviarSugerencia,
        confirmar,
        reintentar,
        nuevaConsulta,
    };
}

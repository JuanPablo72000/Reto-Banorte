"use client";

import { useState, FormEvent } from "react";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { AssistantResponse, CHAT_CARD_REGISTRY, WELCOME_TEXT } from "./types";

export function ChatWindow() {
    const [current, setCurrent] = useState<AssistantResponse>({ text: WELCOME_TEXT });
    const [draft, setDraft] = useState("");

    function handleSend(e: FormEvent) {
        e.preventDefault();
        if (!draft.trim()) return;

        // ⚠️ PENDIENTE DE INTEGRACIÓN CON CAIN/MCP ⚠️
        // Por ahora no se envía nada a ningún backend. Cuando se conecte Cain:
        // este handler debe enviar `draft`, recibir { text, card } como
        // AssistantResponse real, y hacer setCurrent con eso.
        setCurrent({ text: `Recibido: "${draft.trim()}" (respuesta simulada)` });
        setDraft("");
    }

    const CardComponent = current.card ? CHAT_CARD_REGISTRY[current.card] : null;

    return (
        <div className="flex h-full flex-col items-center justify-between p-6">
            <div className="flex w-full max-w-2xl flex-1 flex-col items-center justify-center gap-6 overflow-y-auto text-center">
                <h1 className="text-3xl font-semibold text-[var(--color-text)] sm:text-4xl">
                    {current.text}
                </h1>

                {CardComponent && (
                    <div className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] p-4 text-left">
                        <CardComponent />
                    </div>
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
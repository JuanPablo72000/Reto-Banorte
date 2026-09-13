"use client";

import { useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Icon } from "@/components/ui/Icon";

// Campo de escribir del chat: pill con botón circular de enviar, estados
// de envío, error con role="alert" y foco de regreso al input.
export function ChatComposer({
    onSend,
    sending,
    disabled = false,
    label = "Escribe tu mensaje",
    hint = "Escribe y pulsa Enter para enviar",
    placeholder = "Escribe tu mensaje…",
}: {
    onSend: (texto: string) => void | Promise<void>;
    sending?: boolean;
    disabled?: boolean;
    label?: string;
    hint?: string;
    placeholder?: string;
}) {
    const uid = useId();
    const inputRef = useRef<HTMLInputElement | null>(null);
    const [texto, setTexto] = useState("");
    const [interno, setInterno] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const ocupado = sending ?? interno;
    const hintId = `${uid}-hint`;
    const errId = `${uid}-err`;

    async function enviar(e?: FormEvent) {
        e?.preventDefault();
        const limpio = texto.trim();
        if (!limpio || ocupado || disabled) return;
        setError(null);
        setInterno(true);
        try {
            await onSend(limpio);
            setTexto("");
        } catch {
            setError("No se pudo enviar el mensaje. Intenta de nuevo.");
        } finally {
            setInterno(false);
            inputRef.current?.focus();
        }
    }

    return (
        <form
            onSubmit={enviar}
            aria-label="Enviar mensaje al asistente"
            className="flex items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)] py-1 pl-4 pr-1 shadow-[var(--shadow-1)] focus-within:border-[var(--color-accent)] focus-within:ring-2 focus-within:ring-[var(--color-accent)]"
        >
            <input
                ref={inputRef}
                type="text"
                enterKeyHint="send"
                autoComplete="off"
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                aria-label={label}
                aria-describedby={`${hintId}${error ? ` ${errId}` : ""}`}
                aria-invalid={error ? true : undefined}
                disabled={disabled || ocupado}
                placeholder={placeholder}
                className="min-h-[calc(var(--target-min)-8px)] flex-1 bg-transparent text-base text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none disabled:opacity-60"
            />
            <span id={hintId} className="sr-only">
                {hint}
            </span>
            {error && (
                <p id={errId} role="alert" className="sr-only">
                    {error}
                </p>
            )}
            <button
                type="submit"
                disabled={disabled || ocupado || texto.trim().length === 0}
                aria-label={ocupado ? "Enviando mensaje" : label}
                className="flex h-11 w-11 sm:h-12 sm:w-12 shrink-0 items-center justify-center rounded-full bg-[var(--color-accent)] text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)] active:scale-[0.96] transition-[transform,background-color] duration-150 motion-reduce:transition-none motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2 disabled:opacity-50 disabled:pointer-events-none"
            >
                {ocupado ? (
                    <svg
                        viewBox="0 0 24 24"
                        width={20}
                        height={20}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2.5}
                        strokeLinecap="round"
                        className="animate-spin motion-reduce:animate-none"
                        aria-hidden="true"
                    >
                        <path d="M12 3a9 9 0 1 0 9 9" />
                    </svg>
                ) : (
                    <Icon name="send" size={20} />
                )}
                <span className="sr-only" role="status">
                    {ocupado ? "Enviando mensaje" : ""}
                </span>
            </button>
        </form>
    );
}

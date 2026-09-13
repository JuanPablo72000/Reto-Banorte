"use client";

import { useEffect, useRef, useState } from "react";

/** Count-up numérico para saldos. Respeta reduced-motion (salto directo). */
export function useCountUp(target: number, durationMs = 900): number {
    const [valor, setValor] = useState(0);
    const frame = useRef<number | null>(null);

    useEffect(() => {
        const reducir =
            typeof window !== "undefined" &&
            (window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
                document.documentElement.getAttribute("data-reduced-motion") === "true");
        if (reducir) {
            // Sin animación: valor final en el siguiente frame (async, sin
            // setState síncrono en el effect).
            frame.current = requestAnimationFrame(() => setValor(target));
            return;
        }
        const inicio = performance.now();
        const paso = (ahora: number) => {
            const t = Math.min(1, (ahora - inicio) / durationMs);
            const eased = 1 - Math.pow(1 - t, 3);
            setValor(target * eased);
            if (t < 1) frame.current = requestAnimationFrame(paso);
        };
        frame.current = requestAnimationFrame(paso);
        return () => {
            if (frame.current !== null) cancelAnimationFrame(frame.current);
        };
    }, [target, durationMs]);

    return valor;
}

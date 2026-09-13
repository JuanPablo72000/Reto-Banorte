"use client";

// Estado compartido de la "vista en vivo" del plan (tamaño / tabla-tarjetas /
// contraste). Antes vivía dentro de PlanRenderer (useVistaEnVivo); ahora es
// un provider para que el panel de accesibilidad y el plan usen el mismo
// estado. Misma clave de localStorage que antes: nada se pierde.

import { ReactNode, createContext, useContext, useEffect, useState } from "react";
import type { VistaEnVivo } from "@/lib/layout";

const VISTA_KEY = "banca-vista-en-vivo";
const VISTA_DEFAULT: VistaEnVivo = { tamano: "auto", vista: "auto", contraste: "auto" };

function leerVista(): VistaEnVivo {
    if (typeof window === "undefined") return VISTA_DEFAULT;
    try {
        const raw = localStorage.getItem(VISTA_KEY);
        if (raw) return { ...VISTA_DEFAULT, ...JSON.parse(raw) };
    } catch {
        // corrupto: default
    }
    return VISTA_DEFAULT;
}

interface VistaContextValue {
    vista: VistaEnVivo;
    setVista: (v: VistaEnVivo | ((prev: VistaEnVivo) => VistaEnVivo)) => void;
}

const VistaContext = createContext<VistaContextValue | null>(null);

export function VistaProvider({ children }: { children: ReactNode }) {
    const [vista, setVista] = useState<VistaEnVivo>(VISTA_DEFAULT);
    const [hidratado, setHidratado] = useState(false);

    useEffect(() => {
        // Hidratación desde localStorage en effect para evitar desajustes
        // de hidratación SSR/CSR.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setVista(leerVista());
        setHidratado(true);
    }, []);

    useEffect(() => {
        if (!hidratado) return;
        try {
            localStorage.setItem(VISTA_KEY, JSON.stringify(vista));
        } catch {
            // almacenamiento lleno/bloqueado: se sigue sin persistir
        }
    }, [vista, hidratado]);

    return (
        <VistaContext.Provider value={{ vista, setVista }}>{children}</VistaContext.Provider>
    );
}

export function useVista(): VistaContextValue {
    const ctx = useContext(VistaContext);
    if (!ctx) throw new Error("useVista debe usarse dentro de un <VistaProvider>");
    return ctx;
}

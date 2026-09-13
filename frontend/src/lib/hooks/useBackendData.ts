"use client";

// Carga datos del backend .NET con fallback: si el backend no está
// disponible (ApiUnavailable) la página sigue con datos demo/mocks.

import { useEffect, useRef, useState } from "react";
import { ApiUnavailable } from "@/lib/api/backend";

export interface BackendData<T> {
    data: T | null;
    cargando: boolean;
    /** true cuando falló la red (backend apagado): mostrar datos demo. */
    noDisponible: boolean;
    /** error real del backend (401/404/500) distinto a "no disponible". */
    error: string | null;
    reload: () => void;
}

export function useBackendData<T>(
    fetcher: () => Promise<T>,
    deps: unknown[] = [],
): BackendData<T> {
    const [data, setData] = useState<T | null>(null);
    const [cargando, setCargando] = useState(true);
    const [noDisponible, setNoDisponible] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [tick, setTick] = useState(0);

    const fetcherRef = useRef(fetcher);
    useEffect(() => {
        fetcherRef.current = fetcher;
    });

    // Clave serializable de las dependencias (primitivas/objetos planos).
    let claveDeps = "";
    try {
        claveDeps = JSON.stringify(deps) ?? "";
    } catch {
        claveDeps = String(tick);
    }

    useEffect(() => {
        let vivo = true;
        void (async () => {
            try {
                const d = await fetcherRef.current();
                if (!vivo) return;
                setData(d);
                setNoDisponible(false);
                setError(null);
            } catch (e) {
                if (!vivo) return;
                setData(null);
                if (e instanceof ApiUnavailable) {
                    setNoDisponible(true);
                } else {
                    setError(e instanceof Error ? e.message : "error desconocido");
                }
            } finally {
                if (vivo) setCargando(false);
            }
        })();
        return () => {
            vivo = false;
        };
    }, [claveDeps, tick]);

    return {
        data,
        cargando,
        noDisponible,
        error,
        reload: () => {
            setCargando(true);
            setTick((t) => t + 1);
        },
    };
}

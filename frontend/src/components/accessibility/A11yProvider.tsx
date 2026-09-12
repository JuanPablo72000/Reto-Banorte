"use client";

import { ReactNode, createContext, useContext, useEffect, useState } from "react";

type Theme = "light" | "dark";
type Contrast = "normal" | "high";
export type Palette = "normal" | "colorblind" | "mono";

interface A11yState {
    theme: Theme;
    contrast: Contrast;
    fontScale: number;
    reducedMotion: boolean;
    palette: Palette;
}

interface A11yContextValue extends A11yState {
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
    setContrast: (contrast: Contrast) => void;
    toggleContrast: () => void;
    setFontScale: (scale: number) => void;
    setReducedMotion: (value: boolean) => void;
    setPalette: (palette: Palette) => void;
}

const STORAGE_KEY = "banca-a11y-preferences";

const defaultState: A11yState = {
    theme: "light",
    contrast: "normal",
    fontScale: 1,
    reducedMotion: false,
    palette: "normal",
};

const A11yContext = createContext<A11yContextValue | null>(null);

/**
 * Provider global de accesibilidad. Envolver toda la app una sola vez en
 * layout.tsx. Sincroniza el estado con atributos data-* en <html>, que es
 * lo que globals.css usa para cambiar las variables de color/tamaño/movimiento.
 *
 * `palette` es la paleta de color activa (normal / colorblind / mono).
 * "mono" también actúa como modo oscuro, ya que define sus propios colores
 * oscuros de superficie/texto — no depende de `theme` para eso.
 *
 * ⚠️ PENDIENTE DE INTEGRACIÓN CON CAIN/MCP ⚠️
 * `setPalette` está pensado para que Cain lo dispare cuando la IA decida
 * cambiar la paleta (ej. detecta usuario con daltonismo, o pide modo oscuro).
 * Hoy solo se puede llamar manualmente vía useA11y(); falta el punto donde
 * la respuesta de Cain invoque esta función automáticamente.
 *
 * En el proyecto real, este estado también se sincroniza contra
 * GET/PUT /me/preferences (vía Cain) para persistir la preferencia del usuario.
 */
export function A11yProvider({ children }: { children: ReactNode }) {
    const [state, setState] = useState<A11yState>(defaultState);

    // Cargar preferencia guardada localmente al montar (placeholder mientras
    // se conecta a /me/preferences vía Cain).
    useEffect(() => {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                setState({ ...defaultState, ...JSON.parse(saved) });
            } catch {
                // valor corrupto, se ignora y se usa el default
            }
        } else {
            const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
            setState((prev) => ({ ...prev, reducedMotion: prefersReducedMotion }));
        }
    }, []);

    // Reflejar el estado en el <html> y persistirlo
    useEffect(() => {
        const root = document.documentElement;
        root.setAttribute("data-theme", state.theme);
        root.setAttribute("data-contrast", state.contrast === "high" ? "high" : "normal");
        root.setAttribute("data-reduced-motion", String(state.reducedMotion));
        root.setAttribute("data-palette", state.palette);
        root.style.setProperty("--font-scale", String(state.fontScale));
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }, [state]);

    const value: A11yContextValue = {
        ...state,
        setTheme: (theme) => setState((prev) => ({ ...prev, theme })),
        toggleTheme: () =>
            setState((prev) => ({ ...prev, theme: prev.theme === "light" ? "dark" : "light" })),
        setContrast: (contrast) => setState((prev) => ({ ...prev, contrast })),
        toggleContrast: () =>
            setState((prev) => ({ ...prev, contrast: prev.contrast === "normal" ? "high" : "normal" })),
        setFontScale: (fontScale) => setState((prev) => ({ ...prev, fontScale })),
        setReducedMotion: (reducedMotion) => setState((prev) => ({ ...prev, reducedMotion })),
        setPalette: (palette) => setState((prev) => ({ ...prev, palette })),
    };

    return <A11yContext.Provider value={value}>{children}</A11yContext.Provider>;
}

export function useA11y(): A11yContextValue {
    const context = useContext(A11yContext);
    if (!context) {
        throw new Error("useA11y debe usarse dentro de un <A11yProvider>");
    }
    return context;
}
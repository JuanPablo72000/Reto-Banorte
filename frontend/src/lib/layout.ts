"use client";

import { useEffect, useState } from "react";
import type { AccessibilityTemplate, ExecutedStep } from "@/lib/types/action-plan";

// Motor de layout por x_position — espejo de PositionMetadata
// (mcp/app/schemas/schemas.py) + plantillas fijas
// (mcp/app/ia/accessibility_templates.py). Ningún elemento decide su
// lugar ni su tamaño: todo sale de aquí.

export type Seccion = "header" | "main" | "sidebar" | "footer" | "modal" | "inline" | "notification";
export type Tamano = "sm" | "md" | "lg";

export interface Posicion {
    section: Seccion;
    display_order: number;
    priority: string;
}

const POSICION_DEFAULT: Posicion = { section: "main", display_order: 1, priority: "medium" };

const SECCIONES_VALIDAS: Seccion[] = [
    "header",
    "main",
    "sidebar",
    "footer",
    "modal",
    "inline",
    "notification",
];

// Valores espejo de ACCESSIBILITY_TEMPLATES (fuente real: el .py).
const PLANTILLA_TAMANO: Record<AccessibilityTemplate, { size: Tamano; fontScale: number }> = {
    default: { size: "md", fontScale: 1 },
    senior: { size: "lg", fontScale: 1.5 },
    low_vision: { size: "lg", fontScale: 1.75 },
    blind_screen_reader: { size: "lg", fontScale: 1.25 },
    color_blind_protanopia: { size: "md", fontScale: 1 },
    color_blind_deuteranopia: { size: "md", fontScale: 1 },
    color_blind_tritanopia: { size: "md", fontScale: 1 },
    motor_impairment: { size: "lg", fontScale: 1.25 },
    cognitive_impairment: { size: "lg", fontScale: 1.15 },
    low_literacy: { size: "md", fontScale: 1.15 },
};

function leerPosicionItem(item: unknown): Posicion {
    if (!item || typeof item !== "object") return POSICION_DEFAULT;
    const x = (item as { x_position?: Partial<Posicion> }).x_position;
    if (!x || typeof x !== "object") return POSICION_DEFAULT;
    const section = SECCIONES_VALIDAS.includes(x.section as Seccion)
        ? (x.section as Seccion)
        : POSICION_DEFAULT.section;
    return {
        section,
        display_order: typeof x.display_order === "number" ? x.display_order : 1,
        priority: typeof x.priority === "string" ? x.priority : "medium",
    };
}

/** Posición efectiva de un step: la de su primer resultado (todas las
 *  filas de una tool comparten x_position); sin resultados, main según
 *  índice del step. */
export function posicionDeStep(step: ExecutedStep, indice: number): Posicion {
    const r = step.result as
        | { total: number; muestra: unknown[] }
        | Record<string, unknown>
        | undefined;
    const items = Array.isArray(r) ? r : Array.isArray(r?.muestra) ? r.muestra : r ? [r] : [];
    if (items.length === 0) return { ...POSICION_DEFAULT, display_order: indice + 1 };
    const base = leerPosicionItem(items[0]);
    return { ...base, display_order: base.display_order * 100 + indice };
}

export function agruparPorSeccion(steps: ExecutedStep[]): Record<Seccion, ExecutedStep[]> {
    const grupos: Record<Seccion, ExecutedStep[]> = {
        header: [],
        main: [],
        sidebar: [],
        footer: [],
        modal: [],
        inline: [],
        notification: [],
    };
    steps.forEach((step, i) => {
        grupos[posicionDeStep(step, i).section].push(step);
    });
    for (const s of SECCIONES_VALIDAS) {
        grupos[s].sort(
            (a, b) =>
                posicionDeStep(a, steps.indexOf(a)).display_order -
                posicionDeStep(b, steps.indexOf(b)).display_order,
        );
    }
    return grupos;
}

// --- Tamaños: plantilla IA + override en vivo (ViewControls) ---

export interface VistaEnVivo {
    tamano: "auto" | Tamano;
    vista: "auto" | "tabla" | "tarjetas";
    contraste: "auto" | "normal" | "high";
}

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

export function useVistaEnVivo() {
    const [vista, setVista] = useState<VistaEnVivo>(leerVista);
    useEffect(() => {
        try {
            localStorage.setItem(VISTA_KEY, JSON.stringify(vista));
        } catch {
            // almacenamiento lleno/bloqueado: se sigue sin persistir
        }
    }, [vista]);
    return [vista, setVista] as const;
}

/** Tamaño efectivo: el override en vivo gana a la plantilla de la IA. */
export function tamanoEfectivo(plantilla: AccessibilityTemplate, vista: VistaEnVivo): {
    size: Tamano;
    fontScale: number;
} {
    const base = PLANTILLA_TAMANO[plantilla] ?? PLANTILLA_TAMANO.default;
    return {
        size: vista.tamano === "auto" ? base.size : vista.tamano,
        fontScale: base.fontScale,
    };
}

export function tamanoBoton(size: Tamano): "sm" | "md" | "lg" {
    return size;
}

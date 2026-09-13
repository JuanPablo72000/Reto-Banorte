"use client";

import type { CSSProperties } from "react";
import type { AnimationKind } from "@/lib/types/action-plan";

// Atributos visuales del plan (cherry-pick de plan-visual.tsx de Qwen,
// adaptado a NUESTROS tipos): animación por token + stagger por orden.
// textMode/size los resuelven lib/layout.ts + plantillas, no la IA.
export type { AnimationKind };

export function attrsAnimacion(animation?: string | null, displayOrder?: number | null): {
    "data-animation": AnimationKind;
    style?: CSSProperties;
} {
    // Todo entra animado: si la IA no pide slide/pulse, se usa fade con
    // stagger por orden (reduced-motion lo apaga el CSS global).
    const anim: AnimationKind =
        animation === "slide" || animation === "pulse" ? animation : "fade";
    const orden = typeof displayOrder === "number" ? displayOrder : 0;
    return {
        "data-animation": anim,
        style: { "--orden": String(orden) } as CSSProperties,
    };
}

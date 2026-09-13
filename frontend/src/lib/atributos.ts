"use client";

import type { CSSProperties } from "react";
import type { AnimationKind } from "@/lib/types/action-plan";

// Atributos visuales del plan (cherry-pick de plan-visual.tsx de Qwen,
// adaptado a NUESTROS tipos): animación por token + stagger por orden.
// textMode/size los resuelven lib/layout.ts + plantillas, no la IA.
export type { AnimationKind };

export function attrsAnimacion(animation?: string | null, displayOrder?: number | null): {
    "data-animation"?: AnimationKind;
    style?: CSSProperties;
} {
    const out: { "data-animation"?: AnimationKind; style?: CSSProperties } = {};
    if (animation === "fade" || animation === "slide" || animation === "pulse") {
        out["data-animation"] = animation;
    }
    const orden = typeof displayOrder === "number" ? displayOrder : 0;
    if (orden > 0 || out["data-animation"]) {
        out.style = { "--orden": String(orden) } as CSSProperties;
    }
    return out;
}

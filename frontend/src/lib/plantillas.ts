"use client";

// Aplicación de plantillas de accesibilidad sobre A11yProvider.
// Compartido por PlanRenderer (plantilla que manda la IA) y el panel de
// accesibilidad (plantilla elegida a mano).
import type { useA11y } from "@/components/accessibility/A11yProvider";
import type { AccessibilityTemplate } from "@/lib/types/action-plan";

export const PLANTILLAS_ETIQUETA: Record<AccessibilityTemplate, string> = {
    default: "Predeterminada",
    senior: "Adulto mayor",
    low_vision: "Baja visión",
    blind_screen_reader: "Ceguera (lector de pantalla)",
    color_blind_protanopia: "Daltonismo (protanopía)",
    color_blind_deuteranopia: "Daltonismo (deuteranopía)",
    color_blind_tritanopia: "Daltonismo (tritanopía)",
    motor_impairment: "Movilidad reducida",
    cognitive_impairment: "Impairment cognitivo",
    low_literacy: "Lectura simplificada",
};

export function aplicarPlantilla(
    plantilla: AccessibilityTemplate,
    usar: ReturnType<typeof useA11y>,
    tocarContraste = true,
) {
    // Solo plantillas no-default pisan preferencias (nunca se resetea
    // lo del usuario cuando el plan trae "default"). Con override manual
    // de contraste en vivo, el usuario manda y no se toca.
    if (plantilla === "low_vision") {
        usar.setFontScale(1.75);
        if (tocarContraste) usar.setContrast("high");
    } else if (plantilla === "senior") {
        usar.setFontScale(1.5);
    } else if (plantilla === "motor_impairment") {
        usar.setFontScale(1.25);
    } else if (plantilla === "cognitive_impairment" || plantilla === "low_literacy") {
        usar.setFontScale(1.15);
    } else if (plantilla.startsWith("color_blind")) {
        usar.setPalette("colorblind");
    } else if (plantilla === "blind_screen_reader") {
        usar.setFontScale(1.25);
    }
}

/** Aplicación manual desde el panel: "default" sí restablece la base. */
export function aplicarPlantillaManual(
    plantilla: AccessibilityTemplate,
    usar: ReturnType<typeof useA11y>,
) {
    if (plantilla === "default") {
        usar.setFontScale(1);
        usar.setContrast("normal");
        usar.setPalette("normal");
        return;
    }
    aplicarPlantilla(plantilla, usar);
}

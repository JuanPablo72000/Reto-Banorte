"use client";

// Bloque "Preguntar a Cain": dispara un tool MCP exacto vía accion_directa
// (ejecución garantizada, sin depender de que la IA reinterprete el texto)
// y renderiza el plan resultante con PlanRenderer. Se usa en las páginas
// del menú bancario para los flujos con IA.

import { Button } from "@/components/ui/Button";
import { Icon, type IconExtra } from "@/components/ui/Icon";
import { ErrorState } from "@/components/states/ErrorState";
import { GenerandoPanel } from "@/components/chat/GenerandoPanel";
import { PlanRenderer } from "@/components/chat/PlanRenderer";
import { useChatPlan } from "@/lib/hooks/useChatPlan";
import type { IconType, ToolName } from "@/lib/types/action-plan";

export function CainQuery({
    label,
    tool,
    args = {},
    icon = "sparkle",
    variant = "secondary",
    titulo,
}: {
    label: string;
    tool: ToolName;
    args?: Record<string, unknown>;
    icon?: IconType | IconExtra;
    variant?: "primary" | "secondary" | "ghost";
    titulo?: string;
}) {
    const chat = useChatPlan();

    return (
        <section aria-label={titulo ?? label} className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center gap-3">
                <Button
                    variant={variant}
                    onClick={() =>
                        void chat.enviar(label, { accion_directa: { tool, arguments: args, label } })
                    }
                    disabled={chat.cargando}
                >
                    <Icon name={chat.cargando ? "clock" : icon} size={18} />
                    {label}
                </Button>
                {chat.plan && !chat.cargando && (
                    <Button variant="ghost" size="sm" onClick={chat.nuevaConsulta}>
                        <Icon name="refresh" size={16} /> Limpiar
                    </Button>
                )}
            </div>

            {chat.cargando && <GenerandoPanel etiqueta={`Generando: ${label}`} />}
            {chat.error && (
                <ErrorState description={chat.error} onRetry={chat.ultimoMensaje ? chat.reintentar : undefined} />
            )}
            {chat.plan && !chat.cargando && !chat.error && (
                <PlanRenderer plan={chat.plan} onSugerencia={chat.enviarSugerencia} onConfirmar={chat.confirmar} />
            )}
        </section>
    );
}

"use client";

// Home: chat + interfaces generadas.
// Desktop: 2 paneles (chat izq. con composer anclado, resultados der. con
// scroll propio). Móvil: control segmentado Chat|Resultados con el composer
// SIEMPRE fijo abajo. La lógica vive en useChatPlan (contrato /api/chat
// intacto).

import { useEffect, useRef, useState } from "react";
import { ErrorState } from "@/components/states/ErrorState";
import { FloatingButton } from "@/components/ui/FloatingButton";
import { Icon, type IconExtra } from "@/components/ui/Icon";
import { IconButton } from "@/components/ui/IconButton";
import { useChatPlan } from "@/lib/hooks/useChatPlan";
import type { IconType, ToolName } from "@/lib/types/action-plan";
import { ChatComposer } from "./ChatComposer";
import { GenerandoPanel } from "./GenerandoPanel";
import { PlanRenderer } from "./PlanRenderer";
import { WELCOME_TEXT } from "./types";

const ACCESOS_RAPIDOS: { label: string; tool: ToolName; icon: IconType | IconExtra }[] = [
    { label: "Ver mis cuentas", tool: "get_accounts", icon: "account" },
    { label: "Movimientos recientes", tool: "get_all_transactions", icon: "transaction" },
    { label: "Resumen de mi saldo", tool: "get_account_summary", icon: "balance" },
    { label: "¿Cómo van mis presupuestos?", tool: "get_budgets_monthly", icon: "budget" },
];

type PanelMovil = "chat" | "plan";

export function ChatWindow() {
    const chat = useChatPlan();
    const [panel, setPanel] = useState<PanelMovil>("chat");
    const [fabVisible, setFabVisible] = useState(false);
    const resultadosRef = useRef<HTMLDivElement>(null);
    const hiloRef = useRef<HTMLDivElement>(null);

    // Al generar/llegar un plan, el móvil salta a Resultados.
    // Ajuste de estado derivado durante el render (patrón React).
    const hayContenido = Boolean(chat.plan || chat.cargando || chat.error);
    const [huboContenido, setHuboContenido] = useState(false);
    if (hayContenido && !huboContenido) {
        setHuboContenido(true);
        setPanel("plan");
    } else if (!hayContenido && huboContenido) {
        setHuboContenido(false);
    }

    // El hilo de chat scrollea al final con cada mensaje
    useEffect(() => {
        const el = hiloRef.current;
        if (el) el.scrollTop = el.scrollHeight;
    }, [chat.hilo]);

    function enviarRapido(label: string, tool: ToolName) {
        if (chat.cargando) return;
        void chat.enviar(label, { accion_directa: { tool, arguments: {}, label } });
    }

    function onScrollResultados() {
        const el = resultadosRef.current;
        if (el) setFabVisible(el.scrollTop > 240);
    }

    function irArriba() {
        resultadosRef.current?.scrollTo({ top: 0, behavior: "smooth" });
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    return (
        <div className="flex h-full flex-col lg:h-[calc(100dvh-var(--topbar-h))] lg:flex-row">
            {/* Selector móvil */}
            <div className="flex shrink-0 gap-1 border-b border-[var(--color-border)] p-2 lg:hidden" role="tablist" aria-label="Secciones">
                {(["chat", "plan"] as const).map((p) => (
                    <button
                        key={p}
                        role="tab"
                        type="button"
                        aria-selected={panel === p}
                        onClick={() => setPanel(p)}
                        className={[
                            "flex min-h-[44px] flex-1 items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-colors motion-reduce:transition-none",
                            panel === p
                                ? "bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)]",
                        ].join(" ")}
                    >
                        <Icon name={p === "chat" ? "sparkle" : "grid"} size={18} />
                        {p === "chat" ? "Chat" : "Resultados"}
                        {p === "plan" && chat.cargando && (
                            <span className="ui-blink h-2 w-2 rounded-full bg-current" aria-hidden="true" />
                        )}
                    </button>
                ))}
            </div>

            {/* Panel de chat */}
            <section
                aria-label="Chat con el asistente"
                className={[
                    "min-w-0 flex-1 flex-col lg:flex lg:w-[24rem] lg:shrink-0 lg:flex-none lg:border-r lg:border-[var(--color-border)]",
                    panel === "chat" ? "flex" : "hidden",
                ].join(" ")}
            >
                <header className="flex shrink-0 items-center justify-between gap-2 border-b border-[var(--color-border)] px-4 py-3">
                    <div className="flex items-center gap-2.5">
                        <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-accent)] text-[var(--color-accent-text)]">
                            <Icon name="sparkle" size={18} />
                            <span className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[var(--color-surface)] bg-[var(--color-success-bg)]" aria-hidden="true" />
                        </span>
                        <span className="flex flex-col leading-tight">
                            <span className="text-sm font-semibold text-[var(--color-text)]">Asistente bancario</span>
                            <span className="text-xs text-[var(--color-text-muted)]">En línea · responde al instante</span>
                        </span>
                    </div>
                    <IconButton
                        icon={<Icon name="plus" size={20} />}
                        aria-label="Iniciar nueva consulta"
                        title="Nueva consulta"
                        variant="ghost"
                        onClick={chat.nuevaConsulta}
                    />
                </header>

                <div ref={hiloRef} className="flex-1 overflow-y-auto px-4 py-4">
                    {chat.hilo.length === 0 ? (
                        <div className="ui-rise flex h-full flex-col items-center justify-center gap-4 text-center">
                            <span className="logo-shine flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-[var(--shadow-1)]">
                                <Icon name="sparkle" size={26} />
                            </span>
                            <p className="max-w-xs text-base font-medium text-[var(--color-text)]">{WELCOME_TEXT}</p>
                            <p className="max-w-xs text-sm text-[var(--color-text-muted)]">
                                Escribe lo que necesitas o usa un acceso rápido. La interfaz aparecerá en el panel de resultados.
                            </p>
                        </div>
                    ) : (
                        <ol className="flex flex-col gap-3" aria-label="Conversación">
                            {chat.hilo.map((m, i) => (
                                <li
                                    key={i}
                                    className={[
                                        "ui-rise flex",
                                        m.rol === "user" ? "justify-end" : "justify-start",
                                    ].join(" ")}
                                    style={{ "--orden": Math.min(i, 6) } as React.CSSProperties}
                                >
                                    <p
                                        className={[
                                            "max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm shadow-[var(--shadow-1)]",
                                            m.rol === "user"
                                                ? "rounded-br-md bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                                : "rounded-bl-md border border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-text)]",
                                        ].join(" ")}
                                    >
                                        {m.texto}
                                    </p>
                                </li>
                            ))}
                        </ol>
                    )}
                </div>

                {/* Composer anclado al fondo del panel (desktop) */}
                <div className="hidden shrink-0 border-t border-[var(--color-border)] p-3 lg:block">
                    <ChatComposer onSend={(t) => chat.enviar(t)} sending={chat.cargando} />
                </div>
            </section>

            {/* Panel de resultados */}
            <section
                aria-label="Interfaces generadas"
                className={[
                    "relative min-w-0 flex-1",
                    panel === "plan" ? "block" : "hidden lg:block",
                ].join(" ")}
            >
                <div
                    ref={resultadosRef}
                    onScroll={onScrollResultados}
                    className="h-full overflow-y-auto px-4 py-5 pb-[calc(var(--bottomnav-h)+6.5rem)] lg:px-8 lg:pb-10"
                >
                    {chat.cargando && (
                        <div className="mx-auto max-w-3xl">
                            <GenerandoPanel />
                        </div>
                    )}

                    {!chat.cargando && chat.error && (
                        <div className="mx-auto max-w-3xl">
                            <ErrorState description={chat.error} onRetry={chat.ultimoMensaje ? chat.reintentar : undefined} />
                        </div>
                    )}

                    {!chat.cargando && !chat.error && chat.plan && (
                        <div className="mx-auto max-w-5xl">
                            <PlanRenderer
                                plan={chat.plan}
                                onSugerencia={chat.enviarSugerencia}
                                onConfirmar={chat.confirmar}
                            />
                        </div>
                    )}

                    {!hayContenido && (
                        <div className="mx-auto flex max-w-3xl flex-col gap-6 py-6">
                            <div className="ui-rise flex flex-col gap-2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-6 shadow-[var(--shadow-1)] sm:p-8">
                                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)]">
                                    <Icon name="grid" size={22} />
                                </span>
                                <h2 className="mt-2 text-xl font-semibold text-[var(--color-text)]">
                                    Tus interfaces aparecerán aquí
                                </h2>
                                <p className="text-sm text-[var(--color-text-muted)]">
                                    El asistente genera tablas, tarjetas y gráficas adaptadas a ti. Cada respuesta se anima al acomodarse en este panel.
                                </p>
                            </div>
                            <div className="flex flex-col gap-3" aria-label="Accesos rápidos">
                                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                                    Prueba con…
                                </p>
                                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                    {ACCESOS_RAPIDOS.map((a, i) => (
                                        <button
                                            key={a.tool}
                                            type="button"
                                            onClick={() => enviarRapido(a.label, a.tool)}
                                            className="ui-rise card-hover flex min-h-[var(--target-min)] items-center gap-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-3 text-left text-sm font-medium text-[var(--color-text)] shadow-[var(--shadow-1)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-accent)]"
                                            style={{ "--orden": i + 1 } as React.CSSProperties}
                                        >
                                            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-surface-2)] text-[var(--color-accent)]">
                                                <Icon name={a.icon} size={20} />
                                            </span>
                                            {a.label}
                                            <Icon name="chevron-right" size={16} className="ml-auto text-[var(--color-text-muted)]" />
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {fabVisible && (
                    <FloatingButton
                        position="bottom-right"
                        variant="primary"
                        size="md"
                        label="Ir arriba"
                        onClick={irArriba}
                        icon={<Icon name="arrow-up" size={22} />}
                        aria-label="Volver al inicio de los resultados"
                    />
                )}
            </section>

            {/* Composer fijo abajo (móvil) — nunca lo empuja la interfaz generada */}
            <div className="fixed inset-x-0 bottom-[calc(var(--bottomnav-h)+env(safe-area-inset-bottom))] z-40 border-t border-[var(--color-border)] bg-[var(--color-surface)] p-3 lg:hidden">
                <ChatComposer onSend={(t) => chat.enviar(t)} sending={chat.cargando} />
            </div>
        </div>
    );
}

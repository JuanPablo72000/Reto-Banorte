"use client";

// Panel lateral de accesibilidad — OCULTO por defecto. Se abre con el botón
// de la topbar o con Alt+A. Reemplaza a la antigua barra ViewControls:
// tamaño de letra, paleta (daltonismo/mono), tema, contraste, movimiento,
// plantilla IA y vista del plan (tamaño / tabla-tarjetas / contraste).

import { useEffect, useRef, useState } from "react";
import { useA11y, type Palette } from "@/components/accessibility/A11yProvider";
import { useAuth } from "@/components/auth/AuthProvider";
import { useVista } from "@/components/providers/VistaProvider";
import { Icon } from "@/components/ui/Icon";
import { IconButton } from "@/components/ui/IconButton";
import { Switch } from "@/components/ui/Switch";
import { PLANTILLAS_ETIQUETA, aplicarPlantillaManual } from "@/lib/plantillas";
import type { VistaEnVivo } from "@/lib/layout";
import type { AccessibilityTemplate } from "@/lib/types/action-plan";

const FOCUSABLE =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

function Seccion({ titulo, children }: { titulo: string; children: React.ReactNode }) {
    return (
        <section aria-label={titulo} className="flex flex-col gap-3 border-b border-[var(--color-border)] px-5 py-5 last:border-0">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                {titulo}
            </h2>
            {children}
        </section>
    );
}

function OpcionSegmentada<T extends string>({
    etiqueta,
    opciones,
    valor,
    onElegir,
}: {
    etiqueta: string;
    opciones: { valor: T; texto: string; icono?: React.ReactNode }[];
    valor: T;
    onElegir: (v: T) => void;
}) {
    return (
        <div role="group" aria-label={etiqueta} className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-[var(--color-text)]">{etiqueta}</span>
            <div className="flex flex-wrap gap-1.5">
                {opciones.map((o) => {
                    const activa = valor === o.valor;
                    return (
                        <button
                            key={o.valor}
                            type="button"
                            aria-pressed={activa}
                            onClick={() => onElegir(o.valor)}
                            className={[
                                "inline-flex min-h-[44px] items-center gap-1.5 rounded-lg border px-3 py-2 text-sm font-medium",
                                "transition-[background-color,color,border-color,transform] duration-150 motion-reduce:transition-none active:scale-[0.97]",
                                activa
                                    ? "border-[var(--color-accent)] bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                    : "border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                            ].join(" ")}
                        >
                            {o.icono}
                            {o.texto}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

export function AccessibilityPanel({ abierto, onCerrar }: { abierto: boolean; onCerrar: () => void }) {
    const panelRef = useRef<HTMLDivElement>(null);
    const focoPrevio = useRef<HTMLElement | null>(null);

    useEffect(() => {
        if (!abierto) return;
        focoPrevio.current = document.activeElement as HTMLElement;
        const primer = panelRef.current?.querySelector<HTMLElement>(FOCUSABLE);
        primer?.focus();

        function onKey(e: KeyboardEvent) {
            if (e.key === "Escape") {
                onCerrar();
                return;
            }
            if (e.key === "Tab" && panelRef.current) {
                const f = panelRef.current.querySelectorAll<HTMLElement>(FOCUSABLE);
                if (f.length === 0) return;
                const primero = f[0];
                const ultimo = f[f.length - 1];
                if (e.shiftKey && document.activeElement === primero) {
                    e.preventDefault();
                    ultimo.focus();
                } else if (!e.shiftKey && document.activeElement === ultimo) {
                    e.preventDefault();
                    primero.focus();
                }
            }
        }
        document.addEventListener("keydown", onKey);
        return () => {
            document.removeEventListener("keydown", onKey);
            focoPrevio.current?.focus();
        };
    }, [abierto, onCerrar]);

    if (!abierto) return null;

    return (
        <div className="fixed inset-0 z-[70]">
            <div
                aria-hidden="true"
                onClick={onCerrar}
                className="ui-backdrop absolute inset-0 bg-[var(--color-overlay)]"
            />
            <div
                ref={panelRef}
                role="dialog"
                aria-modal="true"
                aria-label="Accesibilidad y apariencia"
                className="ui-drawer-right absolute inset-y-0 right-0 flex w-full max-w-sm flex-col bg-[var(--color-surface)] shadow-[var(--shadow-2)]"
            >
                <header className="flex items-center justify-between border-b border-[var(--color-border)] px-5 py-4">
                    <div className="flex items-center gap-2">
                        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--color-accent)] text-[var(--color-accent-text)]">
                            <Icon name="accessibility" size={20} />
                        </span>
                        <h1 className="text-base font-semibold text-[var(--color-text)]">
                            Accesibilidad
                        </h1>
                    </div>
                    <IconButton icon={<Icon name="close" size={20} />} aria-label="Cerrar panel" onClick={onCerrar} variant="ghost" />
                </header>

                <div className="flex-1 overflow-y-auto">
                    <ControlesAccesibilidad />
                </div>

                <footer className="border-t border-[var(--color-border)] px-5 py-3">
                    <p className="text-xs text-[var(--color-text-muted)]">
                        Atajo: <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-2)] px-1.5 py-0.5 font-mono">Alt</kbd>{" "}
                        + <kbd className="rounded border border-[var(--color-border)] bg-[var(--color-surface-2)] px-1.5 py-0.5 font-mono">A</kbd>
                        · Los cambios se guardan en este dispositivo.
                    </p>
                </footer>
            </div>
        </div>
    );
}

// Controles reutilizables (drawer + página /settings/accessibility).
export function ControlesAccesibilidad() {
    const a11y = useA11y();
    const { vista, setVista } = useVista();
    const { session } = useAuth();
    const [plantilla, setPlantilla] = useState<AccessibilityTemplate>("default");
    const [memoriaEstado, setMemoriaEstado] = useState<"idle" | "confirmando" | "borrando" | "ok" | "error">("idle");
    const [ajustesOk, setAjustesOk] = useState(false);

    function cambiarVista(parche: Partial<VistaEnVivo>) {
        setVista((prev) => ({ ...prev, ...parche }));
        if (parche.contraste) {
            a11y.setContrast(parche.contraste === "high" ? "high" : "normal");
        }
    }

    async function borrarMemoria() {
        setMemoriaEstado("borrando");
        try {
            const res = await fetch("/api/memory/reset", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_user: session?.user.id ?? 1 }),
            });
            setMemoriaEstado(res.ok ? "ok" : "error");
        } catch {
            setMemoriaEstado("error");
        }
    }

    function restablecerAjustes() {
        a11y.setFontScale(1);
        a11y.setContrast("normal");
        a11y.setPalette("normal");
        a11y.setTheme("light");
        a11y.setReducedMotion(false);
        setPlantilla("default");
        setVista({ tamano: "auto", vista: "auto", contraste: "auto" });
        setAjustesOk(true);
    }

    return (
        <>
                    <Seccion titulo="Texto">
                        <div className="flex items-center justify-between gap-3">
                            <span className="text-sm font-medium text-[var(--color-text)]">Tamaño de letra</span>
                            <div className="flex items-center gap-1">
                                <IconButton
                                    icon={<span className="text-sm font-bold">A−</span>}
                                    aria-label="Reducir tamaño de letra"
                                    variant="secondary"
                                    size="sm"
                                    disabled={a11y.fontScale <= 0.85}
                                    onClick={() => a11y.setFontScale(Math.max(0.85, Number((a11y.fontScale - 0.15).toFixed(2))))}
                                />
                                <span role="status" aria-live="polite" className="min-w-[3.5rem] text-center text-sm text-[var(--color-text-muted)]">
                                    {Math.round(a11y.fontScale * 100)}%
                                </span>
                                <IconButton
                                    icon={<span className="text-sm font-bold">A+</span>}
                                    aria-label="Aumentar tamaño de letra"
                                    variant="secondary"
                                    size="sm"
                                    disabled={a11y.fontScale >= 1.75}
                                    onClick={() => a11y.setFontScale(Math.min(1.75, Number((a11y.fontScale + 0.15).toFixed(2))))}
                                />
                            </div>
                        </div>
                    </Seccion>

                    <Seccion titulo="Color y apariencia">
                        <OpcionSegmentada
                            etiqueta="Paleta"
                            valor={a11y.palette}
                            onElegir={(v) => a11y.setPalette(v as Palette)}
                            opciones={[
                                { valor: "normal", texto: "Normal" },
                                { valor: "colorblind", texto: "Daltónica" },
                                { valor: "mono", texto: "Mono (oscura)" },
                            ]}
                        />
                        <label className="flex flex-col gap-1.5">
                            <span className="text-sm font-medium text-[var(--color-text)]">
                                Plantilla de perfil (daltonismo, baja visión…)
                            </span>
                            <select
                                value={plantilla}
                                onChange={(e) => {
                                    const v = e.target.value as AccessibilityTemplate;
                                    setPlantilla(v);
                                    aplicarPlantillaManual(v, a11y);
                                }}
                                className="min-h-[44px] rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-[var(--color-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]"
                            >
                                {(Object.keys(PLANTILLAS_ETIQUETA) as AccessibilityTemplate[]).map((t) => (
                                    <option key={t} value={t}>
                                        {PLANTILLAS_ETIQUETA[t]}
                                    </option>
                                ))}
                            </select>
                        </label>
                        <OpcionSegmentada
                            etiqueta="Tema"
                            valor={a11y.theme}
                            onElegir={(v) => a11y.setTheme(v as "light" | "dark")}
                            opciones={[
                                { valor: "light", texto: "Claro", icono: <Icon name="sun" size={16} /> },
                                { valor: "dark", texto: "Oscuro", icono: <Icon name="moon" size={16} /> },
                            ]}
                        />
                        <Switch
                            label="Alto contraste"
                            hint="Refuerza textos y bordes"
                            checked={a11y.contrast === "high"}
                            onCheckedChange={a11y.toggleContrast}
                        />
                        <Switch
                            label="Movimiento reducido"
                            hint="Apaga animaciones y transiciones"
                            checked={a11y.reducedMotion}
                            onCheckedChange={a11y.setReducedMotion}
                        />
                    </Seccion>

                    <Seccion titulo="Vista de las interfaces generadas">
                        <OpcionSegmentada
                            etiqueta="Tamaño de controles"
                            valor={vista.tamano}
                            onElegir={(v) => cambiarVista({ tamano: v })}
                            opciones={[
                                { valor: "auto", texto: "Auto" },
                                { valor: "sm", texto: "S" },
                                { valor: "md", texto: "M" },
                                { valor: "lg", texto: "L" },
                            ]}
                        />
                        <OpcionSegmentada
                            etiqueta="Datos como"
                            valor={vista.vista}
                            onElegir={(v) => cambiarVista({ vista: v })}
                            opciones={[
                                { valor: "auto", texto: "Auto" },
                                { valor: "tabla", texto: "Tabla", icono: <Icon name="list" size={16} /> },
                                { valor: "tarjetas", texto: "Tarjetas", icono: <Icon name="grid" size={16} /> },
                            ]}
                        />
                        <OpcionSegmentada
                            etiqueta="Contraste del plan"
                            valor={vista.contraste}
                            onElegir={(v) => cambiarVista({ contraste: v })}
                            opciones={[
                                { valor: "auto", texto: "Auto" },
                                { valor: "normal", texto: "Normal" },
                                { valor: "high", texto: "Alto" },
                            ]}
                        />
                    </Seccion>

                    <Seccion titulo="Memoria y datos guardados">
                        <p className="text-sm text-[var(--color-text-muted)]">
                            El asistente recuerda tus ajustes e intenciones entre conversaciones.
                            Aquí puedes borrar esa memoria o restablecer tus preferencias.
                        </p>

                        {memoriaEstado === "idle" || memoriaEstado === "error" ? (
                            <button
                                type="button"
                                onClick={() => setMemoriaEstado("confirmando")}
                                className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg border border-[var(--color-danger-bg)] px-3 text-sm font-medium text-[var(--color-danger-bg)] transition-colors hover:bg-[var(--color-surface-2)] motion-reduce:transition-none"
                            >
                                <Icon name="close" size={16} />
                                Borrar memoria del asistente
                            </button>
                        ) : memoriaEstado === "confirmando" ? (
                            <div className="flex flex-col gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-3">
                                <p className="text-sm font-medium text-[var(--color-text)]">
                                    ¿Seguro? Se olvidará lo que el asistente aprendió de ti.
                                </p>
                                <div className="flex gap-2">
                                    <button
                                        type="button"
                                        onClick={() => void borrarMemoria()}
                                        className="flex min-h-[44px] flex-1 items-center justify-center rounded-lg bg-[var(--color-danger-bg)] px-3 text-sm font-semibold text-[var(--color-danger-text)]"
                                    >
                                        Sí, borrar
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setMemoriaEstado("idle")}
                                        className="flex min-h-[44px] flex-1 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm font-medium text-[var(--color-text)]"
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </div>
                        ) : memoriaEstado === "borrando" ? (
                            <p role="status" className="flex min-h-[44px] items-center gap-2 text-sm text-[var(--color-text-muted)]">
                                <Icon name="clock" size={16} className="ui-spin" /> Borrando memoria…
                            </p>
                        ) : (
                            <p role="status" className="flex min-h-[44px] items-center gap-2 rounded-lg bg-[var(--color-success-bg)] px-3 text-sm font-medium text-[var(--color-success-text)]">
                                <Icon name="check" size={16} /> Memoria del asistente borrada
                            </p>
                        )}
                        {memoriaEstado === "error" && (
                            <p role="alert" className="text-sm text-[var(--color-danger-bg)]">
                                No se pudo borrar (¿el MCP está apagado?). Intenta de nuevo.
                            </p>
                        )}

                        <button
                            type="button"
                            onClick={restablecerAjustes}
                            className="flex min-h-[44px] w-full items-center justify-center gap-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm font-medium text-[var(--color-text)] transition-colors hover:bg-[var(--color-surface-2)] motion-reduce:transition-none"
                        >
                            <Icon name="refresh" size={16} />
                            Restablecer mis ajustes de accesibilidad
                        </button>
                        {ajustesOk && (
                            <p role="status" className="text-sm text-[var(--color-text-muted)]">
                                Ajustes restablecidos a los valores predeterminados.
                            </p>
                        )}
                    </Seccion>
        </>
    );
}

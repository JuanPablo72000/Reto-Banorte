"use client";

// Configuración: perfil, sesión, preferencias de accesibilidad guardadas
// y acceso rápido al panel.

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useA11y } from "@/components/accessibility/A11yProvider";
import { useAuth } from "@/components/auth/AuthProvider";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";

const PALETA_TEXTO: Record<string, string> = {
    normal: "Normal (marca)",
    colorblind: "Daltónica",
    mono: "Monocromática (oscura)",
};

export default function SettingsPage() {
    const { session, logout } = useAuth();
    const a11y = useA11y();
    const router = useRouter();

    return (
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 pb-[calc(var(--bottomnav-h)+2rem)] sm:p-6 lg:pb-8">
            <header className="ui-rise">
                <h2 className="text-xl font-semibold text-[var(--color-text)]">Configuración</h2>
                <p className="text-sm text-[var(--color-text-muted)]">
                    Tu perfil, sesión y preferencias de accesibilidad.
                </p>
            </header>

            <Card className="ui-rise" style={{ "--orden": 1 } as React.CSSProperties}>
                <CardHeader>
                    <CardTitle>Perfil</CardTitle>
                </CardHeader>
                <div className="flex items-center gap-4">
                    <span aria-hidden="true" className="flex h-14 w-14 items-center justify-center rounded-full bg-[var(--color-safe)] text-lg font-bold text-white">
                        {session?.user.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()}
                    </span>
                    <div className="min-w-0">
                        <p className="truncate text-base font-semibold text-[var(--color-text)]">{session?.user.name}</p>
                        <p className="truncate text-sm text-[var(--color-text-muted)]">{session?.user.email}</p>
                        {session?.demo && (
                            <Badge tone="warning" className="mt-1.5">Sesión demo · id_user 1</Badge>
                        )}
                    </div>
                </div>
            </Card>

            <Card className="ui-rise" style={{ "--orden": 2 } as React.CSSProperties}>
                <CardHeader>
                    <CardTitle>Accesibilidad</CardTitle>
                    <Icon name="accessibility" size={20} className="text-[var(--color-accent)]" />
                </CardHeader>
                <p className="text-sm text-[var(--color-text-muted)]">
                    Preferencias activas en este dispositivo:
                </p>
                <ul className="mt-3 grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                    <li className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
                        <span className="text-[var(--color-text-muted)]">Tamaño de letra</span>
                        <span className="font-semibold text-[var(--color-text)]">{Math.round(a11y.fontScale * 100)}%</span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
                        <span className="text-[var(--color-text-muted)]">Paleta</span>
                        <span className="font-semibold text-[var(--color-text)]">{PALETA_TEXTO[a11y.palette] ?? a11y.palette}</span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
                        <span className="text-[var(--color-text-muted)]">Tema</span>
                        <span className="font-semibold text-[var(--color-text)]">{a11y.theme === "dark" ? "Oscuro" : "Claro"}</span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
                        <span className="text-[var(--color-text-muted)]">Contraste</span>
                        <span className="font-semibold text-[var(--color-text)]">{a11y.contrast === "high" ? "Alto" : "Normal"}</span>
                    </li>
                    <li className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
                        <span className="text-[var(--color-text-muted)]">Movimiento reducido</span>
                        <span className="font-semibold text-[var(--color-text)]">{a11y.reducedMotion ? "Sí" : "No"}</span>
                    </li>
                </ul>
                <div className="mt-4 flex flex-wrap gap-3">
                    <Link href="/settings/accessibility">
                        <Button variant="secondary">
                            <Icon name="settings" size={18} /> Ajustar accesibilidad
                        </Button>
                    </Link>
                </div>
            </Card>

            <Card className="ui-rise" style={{ "--orden": 3 } as React.CSSProperties}>
                <CardHeader>
                    <CardTitle>Sesión</CardTitle>
                </CardHeader>
                <p className="text-sm text-[var(--color-text-muted)]">
                    {session?.demo
                        ? "Estás en modo demo: los datos provienen del asistente y de ejemplos locales."
                        : "Sesión autenticada con el servidor (token JWT)."}
                </p>
                <Button
                    variant="danger"
                    className="mt-4"
                    onClick={() => {
                        logout();
                        router.push("/login");
                    }}
                >
                    <Icon name="logout" size={18} /> Cerrar sesión
                </Button>
            </Card>
        </div>
    );
}

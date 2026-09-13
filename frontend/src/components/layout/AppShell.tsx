"use client";

import { ReactNode, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AccessibilityPanel } from "@/components/accessibility/AccessibilityPanel";
import { useAuth } from "@/components/auth/AuthProvider";
import { Icon, type IconExtra } from "@/components/ui/Icon";
import { IconButton } from "@/components/ui/IconButton";
import { SkipLink } from "@/components/ui/SkipLink";
import type { IconType } from "@/lib/types/action-plan";

type Icono = IconType | IconExtra;

interface NavItem {
    href: string;
    label: string;
    icon: Icono;
}

const NAV_PRINCIPAL: NavItem[] = [
    { href: "/", label: "Inicio", icon: "sparkle" },
    { href: "/accounts", label: "Cuentas", icon: "account" },
    { href: "/balance", label: "Saldos", icon: "balance" },
    { href: "/transactions", label: "Movimientos", icon: "transaction" },
    { href: "/transfers", label: "Transferencias", icon: "transfer" },
];

const NAV_SECUNDARIO: NavItem[] = [
    { href: "/statements", label: "Estados de cuenta", icon: "statement" },
    { href: "/cards", label: "Tarjetas", icon: "card" },
    { href: "/budgets", label: "Presupuestos y metas", icon: "budget" },
    { href: "/reconciliation", label: "Conciliación", icon: "shield" },
];

const NAV_CUENTA: NavItem[] = [
    { href: "/settings", label: "Configuración", icon: "settings" },
];

const TODOS: NavItem[] = [...NAV_PRINCIPAL, ...NAV_SECUNDARIO, ...NAV_CUENTA];

const TABS_MOVIL: NavItem[] = [
    { href: "/", label: "Inicio", icon: "home" },
    { href: "/accounts", label: "Cuentas", icon: "account" },
    { href: "/transactions", label: "Movimientos", icon: "transaction" },
    { href: "/transfers", label: "Transferir", icon: "transfer" },
    { href: "/settings", label: "Más", icon: "menu" },
];

function tituloDe(pathname: string): string {
    const exacto = TODOS.find((n) => n.href === pathname);
    if (exacto) return exacto.label;
    const padre = TODOS.filter((n) => n.href !== "/").find((n) => pathname.startsWith(n.href));
    return padre?.label ?? "Banca Personal";
}

function NavLista({ items, onNavegar }: { items: NavItem[]; onNavegar?: () => void }) {
    const pathname = usePathname();
    return (
        <ul className="flex flex-col gap-1">
            {items.map((item) => {
                const activo = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                    <li key={item.href}>
                        <Link
                            href={item.href}
                            onClick={onNavegar}
                            aria-current={activo ? "page" : undefined}
                            className={[
                                "nav-item flex min-h-[44px] items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
                                activo
                                    ? "bg-[var(--color-accent)] text-[var(--color-accent-text)]"
                                    : "text-[var(--color-text)] hover:bg-[var(--color-surface-2)]",
                            ].join(" ")}
                        >
                            <Icon name={item.icon} size={20} />
                            {item.label}
                        </Link>
                    </li>
                );
            })}
        </ul>
    );
}

function Logo() {
    return (
        <Link href="/" className="flex items-center gap-2.5 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)]">
            <span className="logo-shine flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-[var(--shadow-1)]">
                <Icon name="wallet" size={20} />
            </span>
            <span className="flex flex-col leading-tight">
                <span className="text-sm font-bold text-[var(--color-text)]">Banca Adaptativa</span>
                <span className="text-[0.6875rem] text-[var(--color-text-muted)]">Asistente con IA</span>
            </span>
        </Link>
    );
}

function MenuUsuario() {
    const { session, logout } = useAuth();
    const router = useRouter();
    const [abierto, setAbierto] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!abierto) return;
        function onClick(e: MouseEvent) {
            if (ref.current && !ref.current.contains(e.target as Node)) setAbierto(false);
        }
        function onKey(e: KeyboardEvent) {
            if (e.key === "Escape") setAbierto(false);
        }
        document.addEventListener("mousedown", onClick);
        document.addEventListener("keydown", onKey);
        return () => {
            document.removeEventListener("mousedown", onClick);
            document.removeEventListener("keydown", onKey);
        };
    }, [abierto]);

    if (!session) return null;
    const iniciales = session.user.name
        .split(" ")
        .map((p) => p[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();

    return (
        <div ref={ref} className="relative">
            <button
                type="button"
                onClick={() => setAbierto((v) => !v)}
                aria-expanded={abierto}
                aria-haspopup="menu"
                className="flex min-h-[44px] items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] py-1 pl-1 pr-3 transition-colors hover:bg-[var(--color-surface-2)] motion-reduce:transition-none"
            >
                <span aria-hidden="true" className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-safe)] text-xs font-bold text-white">
                    {iniciales}
                </span>
                <span className="hidden max-w-[8rem] truncate text-sm font-medium text-[var(--color-text)] sm:block">
                    {session.user.name}
                </span>
                <Icon name="chevron-down" size={16} className="text-[var(--color-text-muted)]" />
            </button>
            {abierto && (
                <div
                    role="menu"
                    aria-label="Menú de usuario"
                    className="ui-pop absolute right-0 z-50 mt-2 w-60 overflow-hidden rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-[var(--shadow-2)]"
                >
                    <div className="border-b border-[var(--color-border)] px-4 py-3">
                        <p className="truncate text-sm font-semibold text-[var(--color-text)]">{session.user.name}</p>
                        <p className="truncate text-xs text-[var(--color-text-muted)]">{session.user.email}</p>
                        {session.demo && (
                            <span className="mt-1.5 inline-block rounded-full bg-[var(--color-warning-bg)] px-2 py-0.5 text-[0.6875rem] font-medium text-[var(--color-warning-text)]">
                                Modo demo
                            </span>
                        )}
                    </div>
                    <Link
                        role="menuitem"
                        href="/settings"
                        onClick={() => setAbierto(false)}
                        className="flex min-h-[44px] items-center gap-2.5 px-4 text-sm text-[var(--color-text)] hover:bg-[var(--color-surface-2)]"
                    >
                        <Icon name="settings" size={18} /> Configuración
                    </Link>
                    <button
                        role="menuitem"
                        type="button"
                        onClick={() => {
                            logout();
                            router.push("/login");
                        }}
                        className="flex w-full min-h-[44px] items-center gap-2.5 px-4 text-left text-sm text-[var(--color-danger-bg)] hover:bg-[var(--color-surface-2)]"
                    >
                        <Icon name="logout" size={18} /> Cerrar sesión
                    </button>
                </div>
            )}
        </div>
    );
}

export interface AppShellProps {
    children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
    const pathname = usePathname();
    const [drawer, setDrawer] = useState(false);
    const [panel, setPanel] = useState(false);

    // Alt+A abre/cierra el panel de accesibilidad
    useEffect(() => {
        function onKey(e: KeyboardEvent) {
            if (e.altKey && (e.key === "a" || e.key === "A")) {
                e.preventDefault();
                setPanel((v) => !v);
            }
        }
        document.addEventListener("keydown", onKey);
        return () => document.removeEventListener("keydown", onKey);
    }, []);

    // Cerrar el drawer al navegar (ajuste de estado derivado en render)
    const [rutaPrev, setRutaPrev] = useState(pathname);
    if (rutaPrev !== pathname) {
        setRutaPrev(pathname);
        setDrawer(false);
    }

    return (
        <div className="flex min-h-dvh flex-col bg-[var(--color-surface)] lg:flex-row">
            <SkipLink targetId="main-content" />

            {/* Sidebar desktop */}
            <aside
                aria-label="Navegación principal"
                className="sticky top-0 hidden h-dvh w-[var(--sidebar-w)] shrink-0 flex-col gap-6 border-r border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-5 lg:flex"
            >
                <Logo />
                <nav className="flex flex-1 flex-col gap-6 overflow-y-auto">
                    <NavLista items={NAV_PRINCIPAL} />
                    <div className="flex flex-col gap-1.5">
                        <p className="px-3 text-[0.6875rem] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                            Consultas
                        </p>
                        <NavLista items={NAV_SECUNDARIO} />
                    </div>
                </nav>
                <NavLista items={NAV_CUENTA} />
            </aside>

            {/* Drawer móvil */}
            {drawer && (
                <div className="fixed inset-0 z-[60] lg:hidden">
                    <div aria-hidden="true" className="ui-backdrop absolute inset-0 bg-[var(--color-overlay)]" onClick={() => setDrawer(false)} />
                    <div
                        role="dialog"
                        aria-modal="true"
                        aria-label="Menú de navegación"
                        className="ui-drawer-left absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col gap-6 bg-[var(--color-surface)] px-4 py-5 shadow-[var(--shadow-2)]"
                    >
                        <div className="flex items-center justify-between">
                            <Logo />
                            <IconButton icon={<Icon name="close" size={20} />} aria-label="Cerrar menú" onClick={() => setDrawer(false)} variant="ghost" />
                        </div>
                        <nav className="flex flex-1 flex-col gap-6 overflow-y-auto">
                            <NavLista items={NAV_PRINCIPAL} onNavegar={() => setDrawer(false)} />
                            <NavLista items={NAV_SECUNDARIO} onNavegar={() => setDrawer(false)} />
                            <NavLista items={NAV_CUENTA} onNavegar={() => setDrawer(false)} />
                        </nav>
                    </div>
                </div>
            )}

            <div className="flex min-w-0 flex-1 flex-col">
                {/* Topbar */}
                <header className="sticky top-0 z-40 flex h-[var(--topbar-h)] items-center gap-3 border-b border-[var(--color-border)] bg-[var(--color-surface)] px-4 lg:px-6">
                    <IconButton
                        icon={<Icon name="menu" size={22} />}
                        aria-label="Abrir menú"
                        variant="ghost"
                        className="lg:hidden"
                        onClick={() => setDrawer(true)}
                    />
                    <h1 className="min-w-0 flex-1 truncate text-base font-semibold text-[var(--color-text)] lg:text-lg">
                        {tituloDe(pathname)}
                    </h1>
                    <IconButton
                        icon={<Icon name="accessibility" size={22} />}
                        aria-label="Abrir panel de accesibilidad (Alt+A)"
                        variant="ghost"
                        onClick={() => setPanel(true)}
                    />
                    <MenuUsuario />
                </header>

                <main id="main-content" className="flex-1 pb-[var(--bottomnav-h)] lg:pb-0">
                    <div key={pathname} className="ui-page h-full">
                        {children}
                    </div>
                </main>
            </div>

            {/* Tabs inferiores móvil */}
            <nav
                aria-label="Accesos rápidos"
                className="fixed inset-x-0 bottom-0 z-40 flex h-[var(--bottomnav-h)] items-stretch border-t border-[var(--color-border)] bg-[var(--color-surface)] pb-[env(safe-area-inset-bottom)] lg:hidden"
            >
                {TABS_MOVIL.map((t) => {
                    const activo = t.href === "/" ? pathname === "/" : pathname.startsWith(t.href);
                    return (
                        <Link
                            key={t.href}
                            href={t.href}
                            aria-current={activo ? "page" : undefined}
                            className={[
                                "flex flex-1 flex-col items-center justify-center gap-0.5 text-[0.6875rem] font-medium transition-colors",
                                activo ? "text-[var(--color-accent)]" : "text-[var(--color-text-muted)]",
                            ].join(" ")}
                        >
                            <Icon name={t.icon} size={22} />
                            {t.label}
                        </Link>
                    );
                })}
            </nav>

            <AccessibilityPanel abierto={panel} onCerrar={() => setPanel(false)} />
        </div>
    );
}

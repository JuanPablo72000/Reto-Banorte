"use client";

// Página de login (híbrida): intenta contra /auth/login del backend .NET;
// si el backend no está disponible entra en modo demo. Credenciales del
// seed: demo@banorte.mx / Demo123!

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, useAuth } from "@/components/auth/AuthProvider";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { Input } from "@/components/ui/Input";
import { WELCOME_TEXT } from "@/components/chat/types";

const CARACTERISTICAS = [
    { icon: "sparkle" as const, titulo: "Asistente con IA", texto: "Pregunta en lenguaje natural y la interfaz se genera para ti." },
    { icon: "accessibility" as const, titulo: "Accesibilidad adaptativa", texto: "Paletas para daltonismo, alto contraste, texto grande y más." },
    { icon: "shield" as const, titulo: "Operaciones seguras", texto: "Toda operación sensible pide tu confirmación explícita." },
];

export default function LoginPage() {
    const { session, ready, login, loginDemo } = useAuth();
    const router = useRouter();
    const [email, setEmail] = useState("demo@banorte.mx");
    const [password, setPassword] = useState("Demo123!");
    const [ver, setVer] = useState(false);
    const [enviando, setEnviando] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (ready && session) router.replace("/");
    }, [ready, session, router]);

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        if (enviando) return;
        setEnviando(true);
        setError(null);
        try {
            await login(email.trim(), password);
            router.replace("/");
        } catch (err) {
            if (err instanceof ApiError && err.status === 401) {
                setError("Credenciales incorrectas. Verifica tu correo y contraseña.");
            } else if (err instanceof ApiError) {
                setError(`El servidor respondió con un error (${err.status}). Intenta de nuevo.`);
            } else {
                setError("No se pudo iniciar sesión. Intenta de nuevo.");
            }
        } finally {
            setEnviando(false);
        }
    }

    return (
        <div className="grid min-h-dvh grid-cols-1 lg:grid-cols-2">
            {/* Panel de marca */}
            <div className="login-gradient relative hidden overflow-hidden lg:block" aria-hidden="true">
                <span className="login-blob" style={{ width: 340, height: 340, top: "-60px", left: "-80px" }} />
                <span className="login-blob" style={{ width: 260, height: 260, bottom: "10%", right: "-60px", animationDelay: "-5s" }} />
                <span className="login-blob" style={{ width: 160, height: 160, top: "40%", left: "30%", animationDelay: "-9s" }} />
                <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
                    <div className="flex items-center gap-3">
                        <span className="logo-shine flex h-11 w-11 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
                            <Icon name="wallet" size={24} />
                        </span>
                        <span className="text-lg font-bold">Banca Adaptativa</span>
                    </div>
                    <div className="flex max-w-md flex-col gap-8">
                        <p className="text-3xl font-semibold leading-snug">{WELCOME_TEXT}</p>
                        <ul className="flex flex-col gap-5">
                            {CARACTERISTICAS.map((c, i) => (
                                <li key={c.titulo} className="ui-rise flex items-start gap-3" style={{ "--orden": i + 1 } as React.CSSProperties}>
                                    <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/15 backdrop-blur">
                                        <Icon name={c.icon} size={18} />
                                    </span>
                                    <span>
                                        <span className="block text-sm font-semibold">{c.titulo}</span>
                                        <span className="block text-sm text-white/80">{c.texto}</span>
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <p className="text-xs text-white/70">Demo académica · Reto Banorte</p>
                </div>
            </div>

            {/* Formulario */}
            <div className="flex items-center justify-center bg-[var(--color-surface)] p-6">
                <div className="ui-rise w-full max-w-md" style={{ "--orden": 1 } as React.CSSProperties}>
                    <div className="mb-8 flex flex-col items-center gap-3 text-center lg:hidden">
                        <span className="logo-shine flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-[var(--shadow-1)]">
                            <Icon name="wallet" size={28} />
                        </span>
                        <p className="text-lg font-bold text-[var(--color-text)]">Banca Adaptativa</p>
                    </div>

                    <h1 className="text-2xl font-semibold text-[var(--color-text)]">Inicia sesión</h1>
                    <p className="mt-1 text-sm text-[var(--color-text-muted)]">
                        Accede a tu banca personal con asistente inteligente.
                    </p>

                    <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-5" noValidate>
                        <Input
                            label="Correo electrónico"
                            type="email"
                            name="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="tu@correo.mx"
                        />
                        <div className="relative">
                            <Input
                                label="Contraseña"
                                type={ver ? "text" : "password"}
                                name="password"
                                autoComplete="current-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="pr-12"
                            />
                            <button
                                type="button"
                                onClick={() => setVer((v) => !v)}
                                aria-label={ver ? "Ocultar contraseña" : "Mostrar contraseña"}
                                className="absolute right-1 top-[2.1rem] flex h-11 w-11 items-center justify-center rounded-lg text-[var(--color-text-muted)] transition-colors hover:text-[var(--color-text)] motion-reduce:transition-none"
                            >
                                <Icon name={ver ? "eye-off" : "eye"} size={20} />
                            </button>
                        </div>

                        {error && (
                            <p role="alert" className="ui-pop flex items-start gap-2 rounded-lg border border-[var(--color-danger-bg)] bg-[var(--color-surface-2)] px-3 py-2.5 text-sm text-[var(--color-text)]">
                                <Icon name="warning" size={18} tone="danger" className="mt-0.5 shrink-0" />
                                {error}
                            </p>
                        )}

                        <Button type="submit" variant="primary" size="lg" loading={enviando} className="w-full">
                            {enviando ? "Verificando…" : "Entrar"}
                        </Button>
                    </form>

                    <div className="my-6 flex items-center gap-3" aria-hidden="true">
                        <span className="h-px flex-1 bg-[var(--color-border)]" />
                        <span className="text-xs text-[var(--color-text-muted)]">o</span>
                        <span className="h-px flex-1 bg-[var(--color-border)]" />
                    </div>

                    <Button
                        type="button"
                        variant="secondary"
                        size="lg"
                        className="w-full"
                        onClick={() => {
                            void loginDemo().then(() => router.replace("/"));
                        }}
                    >
                        <Icon name="sparkle" size={18} /> Entrar en modo demo
                    </Button>

                    <p className="mt-6 text-center text-xs text-[var(--color-text-muted)]">
                        Credenciales de prueba: <span className="font-mono">demo@banorte.mx</span> · <span className="font-mono">Demo123!</span>
                        <br />
                        Si el backend no está corriendo, «Entrar» usa el modo demo automáticamente.
                    </p>
                </div>
            </div>
        </div>
    );
}

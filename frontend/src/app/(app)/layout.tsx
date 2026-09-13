"use client";

// Layout autenticado: AppShell (sidebar/topbar/tabs + panel de accesibilidad)
// y VistaProvider (estado compartido de la vista del plan). Si no hay
// sesión, redirige a /login.

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthProvider";
import { AppShell } from "@/components/layout/AppShell";
import { VistaProvider } from "@/components/providers/VistaProvider";
import { Spinner } from "@/components/ui/Spinner";

export default function AppLayout({ children }: { children: React.ReactNode }) {
    const { session, ready } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (ready && !session) router.replace("/login");
    }, [ready, session, router]);

    if (!ready || !session) {
        return (
            <div className="flex min-h-dvh items-center justify-center bg-[var(--color-surface)]" role="status" aria-label="Cargando sesión">
                <Spinner size="lg" label="Cargando tu sesión" />
            </div>
        );
    }

    return (
        <VistaProvider>
            <AppShell>{children}</AppShell>
        </VistaProvider>
    );
}

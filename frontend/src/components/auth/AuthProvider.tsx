"use client";

import { ReactNode, createContext, useContext, useEffect, useState } from "react";
import { ApiError, ApiUnavailable, loginRequest } from "@/lib/api/backend";

export interface SessionUser {
    id: number;
    name: string;
    email: string;
}

export interface Session {
    user: SessionUser;
    token: string | null;
    /** true cuando entró sin backend (modo demo del reto). */
    demo: boolean;
}

interface AuthContextValue {
    session: Session | null;
    /** false hasta rehidratar de localStorage (evita redirects en falso). */
    ready: boolean;
    /**
     * Login híbrido: intenta contra /auth/login del backend .NET; si el
     * backend no está disponible (red/apagado) entra en modo demo con
     * id_user=1. Credenciales inválidas con backend arriba → ApiError 401.
     */
    login: (email: string, password: string) => Promise<Session>;
    loginDemo: () => Promise<Session>;
    logout: () => void;
}

const STORAGE_KEY = "banca-session";

const AuthContext = createContext<AuthContextValue | null>(null);

const USUARIO_DEMO: SessionUser = {
    id: 1,
    name: "Usuario Demo",
    email: "demo@banorte.mx",
};

function leerSesion(): Session | null {
    if (typeof window === "undefined") return null;
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return null;
        const s = JSON.parse(raw) as Session;
        return s?.user ? s : null;
    } catch {
        return null;
    }
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [session, setSession] = useState<Session | null>(null);
    const [ready, setReady] = useState(false);

    useEffect(() => {
        // Hidratación desde localStorage en effect (no en el initializer)
        // para evitar desajustes de hidratación SSR/CSR.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSession(leerSesion());
        setReady(true);
    }, []);

    function guardar(s: Session | null) {
        setSession(s);
        try {
            if (s) localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
            else localStorage.removeItem(STORAGE_KEY);
        } catch {
            // almacenamiento bloqueado: la sesión vive solo en memoria
        }
    }

    async function login(email: string, password: string): Promise<Session> {
        let auth;
        try {
            auth = await loginRequest(email, password);
        } catch (e) {
            if (e instanceof ApiUnavailable) {
                // Backend apagado: modo demo para que la exposición continúe.
                const s: Session = { user: USUARIO_DEMO, token: null, demo: true };
                guardar(s);
                return s;
            }
            throw e;
        }
        const s: Session = {
            user: { id: auth.user.idUser, name: auth.user.name, email: auth.user.email },
            token: auth.token,
            demo: false,
        };
        guardar(s);
        return s;
    }

    async function loginDemo(): Promise<Session> {
        const s: Session = { user: USUARIO_DEMO, token: null, demo: true };
        guardar(s);
        return s;
    }

    return (
        <AuthContext.Provider
            value={{ session, ready, login, loginDemo, logout: () => guardar(null) }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth debe usarse dentro de un <AuthProvider>");
    return ctx;
}

export { ApiError, ApiUnavailable };

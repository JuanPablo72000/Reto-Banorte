// Helpers para leer el `result` de un ExecutedStep.
// El orquestador envuelve listas en { total, muestra[] } y deja los
// objetos únicos tal cual (ver mcp/app/orquestador.py).

type Registro = Record<string, unknown>;

export function lista<T>(result: unknown): T[] {
    if (!result || typeof result !== "object") return [];
    if (Array.isArray(result)) return result as T[];
    const muestra = (result as { muestra?: unknown }).muestra;
    return Array.isArray(muestra) ? (muestra as T[]) : [];
}

export function objeto<T>(result: unknown): T | null {
    if (!result || typeof result !== "object" || Array.isArray(result)) return null;
    const rec = result as Registro;
    if (Array.isArray(rec.muestra)) return (rec.muestra[0] as T) ?? null;
    return result as T;
}

export function campo<T>(obj: Registro | null | undefined, clave: string, defecto: T): T {
    if (!obj || typeof obj !== "object") return defecto;
    const v = obj[clave];
    return (v ?? defecto) as T;
}

const formatoMoneda = new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
});

export function mxn(valor: unknown, moneda = "MXN"): string {
    if (typeof valor !== "number") return "—";
    try {
        return new Intl.NumberFormat("es-MX", { style: "currency", currency: moneda }).format(valor);
    } catch {
        return formatoMoneda.format(valor);
    }
}

export function fecha(valor: unknown): string {
    if (typeof valor !== "string" || !valor) return "—";
    const d = new Date(valor);
    if (Number.isNaN(d.getTime())) return String(valor).slice(0, 10);
    return d.toLocaleDateString("es-MX", { timeZone: "UTC" });
}

// Lenguaje humano para el chat — espejo de presentación de los valores
// técnicos que devuelve la API (BancaAdaptativa.Api) y el MCP.
// Regla acordada: todo estado se humaniza al español, pero solo se
// MUESTRA si aporta información (relevante); posted/active/generated
// se ocultan porque son el caso normal y meten ruido.
import type { Tone } from "./types/action-plan";

const ETIQUETAS_ESTADO: Record<string, string> = {
    // Movimientos / transferencias / conciliación
    posted: "Publicada",
    pending: "Pendiente",
    pending_confirmation: "Por confirmar",
    confirmed: "Confirmada",
    failed: "Fallida",
    reversed: "Revertida",
    matched: "Conciliada",
    mismatch: "No coincide",
    // Cuentas / tarjetas
    active: "Activa",
    blocked: "Bloqueada",
    frozen: "Congelada",
    closed: "Cerrada",
    cancelled: "Cancelada",
    // Estados de cuenta
    generated: "Generado",
    archived: "Archivado",
    // Presupuestos / metas
    exceeded: "Excedido",
    paused: "Pausada",
    completed: "Completada",
};

// Estados que SÍ se muestran (requieren atención o confirman algo).
// El resto (posted, active, generated...) es el caso normal y se oculta.
const ESTADOS_RELEVANTES = new Set([
    "pending",
    "pending_confirmation",
    "confirmed",
    "failed",
    "reversed",
    "mismatch",
    "blocked",
    "frozen",
    "closed",
    "cancelled",
    "exceeded",
    "paused",
    "completed",
    "archived",
]);

export function etiquetaEstado(estado: unknown): string {
    if (typeof estado !== "string" || !estado) return "—";
    return ETIQUETAS_ESTADO[estado] ?? estado.charAt(0).toUpperCase() + estado.slice(1);
}

export function estadoRelevante(estado: unknown): boolean {
    return typeof estado === "string" && ESTADOS_RELEVANTES.has(estado);
}

export function tonoEstado(estado: unknown): Tone {
    if (estado === "archived") return "neutral";
    if (
        estado === "confirmed" ||
        estado === "matched" ||
        estado === "completed" ||
        estado === "active"
    )
        return "success";
    if (
        estado === "failed" ||
        estado === "mismatch" ||
        estado === "reversed" ||
        estado === "blocked" ||
        estado === "frozen" ||
        estado === "closed" ||
        estado === "cancelled" ||
        estado === "exceeded"
    )
        return "danger";
    return "warning";
}

// Categorías reales de la API (seed DbSeeder.cs + catálogo). Lo no
// listado se capitaliza ("mi_categoria" -> "Mi categoria").
const ETIQUETAS_CATEGORIA: Record<string, string> = {
    nomina: "Nómina",
    super: "Súper",
    transporte: "Transporte",
    restaurante: "Restaurantes",
    gasolina: "Gasolina",
    servicios: "Servicios",
    salud: "Salud",
    educacion: "Educación",
    entretenimiento: "Entretenimiento",
    ropa: "Ropa",
    vivienda: "Vivienda",
    ahorro: "Ahorro",
    transferencia: "Transferencia",
    pago: "Pago",
    retiro: "Retiro",
    deposito: "Depósito",
    otro: "Otro",
};

export function etiquetaCategoria(codigo: unknown): string {
    if (typeof codigo !== "string" || !codigo) return "—";
    const conocido = ETIQUETAS_CATEGORIA[codigo.toLowerCase()];
    if (conocido) return conocido;
    return codigo.replace(/[_-]+/g, " ").replace(/^./, (c) => c.toUpperCase());
}

// Claves técnicas que nunca se muestran en el fallback genérico
// (ids, metadata de UI, defaults del protocolo).
const CLAVES_TECNICAS = new Set([
    "id_user",
    "id_account",
    "id_origin_account",
    "id_session",
    "id_transfer",
    "id_statement",
    "id_credit_card",
    "id_match",
    "id_transaction",
    "id_balance",
    "id_preference",
    "id_category",
    "id_expense_category",
    "x_placeholder",
    "x_position",
    "method",
    "limit",
    "currency",
]);

export function esClaveVisible(clave: string): boolean {
    return !CLAVES_TECNICAS.has(clave);
}

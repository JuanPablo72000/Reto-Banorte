import { AccountsList } from "@/components/accounts/AccountsList";
import { BalanceGrid } from "@/components/balance/BalanceGrid";
import { ReconciliationView } from "@/components/reconciliation/ReconciliationView";
import { TransactionsView } from "@/components/transactions/TransactionsView";
import { TransferFlow } from "@/components/transfers/TransferFlow";
import { ComponentType } from "react";

export type ChatCardType =
    | "balances"
    | "transfer"
    | "transactions"
    | "accounts"
    | "reconciliation";

// Respuesta actual del asistente: solo la más reciente se muestra en pantalla,
// no se acumula historial (la interfaz "se transforma", no se apila).
export interface AssistantResponse {
    text: string;
    card?: ChatCardType;
}

export const WELCOME_TEXT =
    "Hola, soy tu asistente de banca personal. ¿En qué te ayudo hoy?";

// Registro de componentes embebibles. Cain/MCP decide CUÁL usar y CUÁNDO —
// el frontend solo expone el catálogo.
// TODO(Cain/MCP): cuando Cain devuelva props reales por tarjeta, este mapa
// tendrá que pasar de ComponentType a algo que acepte props tipadas por card.
export const CHAT_CARD_REGISTRY: Record<ChatCardType, ComponentType> = {
    balances: BalanceGrid,
    transfer: TransferFlow,
    transactions: TransactionsView,
    accounts: AccountsList,
    reconciliation: ReconciliationView,
};
"use client";

import { useState, useCallback } from "react";
import { TransferForm } from "./TransferForm";
import { TransferConfirmation } from "./TransferConfirmation";
import { TransferResult } from "./TransferResult";
import { TransferDraft, TransferStatus } from "./types";

// Contenedor del flujo completo de transferencia.
//
// ⚠️ PENDIENTE DE INTEGRACIÓN CON CAIN ⚠️
// confirmTransferStub() NO habla con ningún backend real todavía.
// Ahora mismo solo resuelve "confirmed" para poder ver el flujo completo
// en el prototipo. Antes de la entrega final hay que reemplazarla por la
// llamada real a Cain (lib/cain-client.ts) y manejar "failed"/"expired"
// según la respuesta real, no aquí.

type FlowStep = "form" | "confirmation" | "result";

async function confirmTransferStub(): Promise<"confirmed" | "failed"> {
    // TODO(Cain): sustituir por la llamada real al backend vía Cain.
    return "confirmed";
}

export function TransferFlow() {
    const [step, setStep] = useState<FlowStep>("form");
    const [draft, setDraft] = useState<TransferDraft | null>(null);
    const [status, setStatus] = useState<TransferStatus>("draft");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleFormSubmit = useCallback((newDraft: TransferDraft) => {
        setDraft(newDraft);
        setStatus("pending_confirmation");
        setStep("confirmation");
    }, []);

    const handleConfirm = useCallback(async () => {
        setIsSubmitting(true);
        const result = await confirmTransferStub();
        setStatus(result);
        setStep("result");
        setIsSubmitting(false);
    }, []);

    const handleCancelConfirmation = useCallback(() => {
        setStatus("cancelled");
        setStep("form");
    }, []);

    const handleRetry = useCallback(() => {
        setStatus("draft");
        setStep("form");
    }, []);

    const handleDone = useCallback(() => {
        setDraft(null);
        setStatus("draft");
        setStep("form");
    }, []);

    return (
        <div className="max-w-md mx-auto w-full">
            {step === "form" && (
                <TransferForm
                    onSubmit={handleFormSubmit}
                    initialDraft={draft ?? undefined}
                />
            )}

            {step === "confirmation" && draft && (
                <TransferConfirmation
                    draft={draft}
                    onConfirm={handleConfirm}
                    onCancel={handleCancelConfirmation}
                    isSubmitting={isSubmitting}
                />
            )}

            {step === "result" && draft && status !== "draft" && status !== "pending_confirmation" && (
                <TransferResult
                    draft={draft}
                    status={status}
                    onDone={handleDone}
                    onRetry={handleRetry}
                />
            )}
        </div>
    );
}
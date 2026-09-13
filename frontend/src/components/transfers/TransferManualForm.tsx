"use client";

import { StepperForm } from "@/components/ui/StepperForm";

// Formulario manual de transferencia (2 pasos). Al confirmar compone el
// mensaje en lenguaje natural y lo entrega al padre, que lo manda por el
// flujo normal del chat (/api/chat -> IA -> modal de confirmación).
export function TransferManualForm({ onListo }: { onListo: (mensaje: string) => void }) {
    return (
        <StepperForm
            tituloForm="Nueva transferencia"
            pasos={[
                {
                    id: "destino",
                    titulo: "¿A quién le envías?",
                    descripcion: "Alias del contacto destino.",
                    campos: [
                        {
                            id: "alias",
                            etiqueta: "Destinatario",
                            tipo: "texto",
                            requerido: true,
                            placeholder: "Ej. Mi hermano",
                        },
                        {
                            id: "concepto",
                            etiqueta: "Concepto (opcional)",
                            tipo: "texto",
                            placeholder: "Ej. Regalo de cumpleaños",
                        },
                    ],
                },
                {
                    id: "monto",
                    titulo: "¿Cuánto envías?",
                    descripcion: "Monto en MXN.",
                    campos: [
                        {
                            id: "monto",
                            etiqueta: "Monto",
                            tipo: "numero",
                            requerido: true,
                            placeholder: "Ej. 500",
                        },
                    ],
                },
            ]}
            onSubmit={(v) => {
                const concepto = (v.concepto ?? "").trim();
                onListo(
                    `transfiere $${v.monto} a ${v.alias.trim()}` +
                        (concepto ? ` por ${concepto}` : ""),
                );
            }}
        />
    );
}

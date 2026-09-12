import { ReactNode, createContext, useCallback, useContext, useState } from "react";

type ToastTone = "success" | "error" | "info" | "warning";

interface ToastMessage {
    id: string;
    tone: ToastTone;
    message: string;
}

interface ToastContextValue {
    showToast: (tone: ToastTone, message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const toneClasses: Record<ToastTone, string> = {
    success: "bg-[var(--color-success-bg)] text-[var(--color-success-text)]",
    error: "bg-[var(--color-danger-bg)] text-[var(--color-danger-text)]",
    warning: "bg-[var(--color-warning-bg)] text-[var(--color-warning-text)]",
    info: "bg-[var(--color-info-bg)] text-[var(--color-info-text)]",
};

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastMessage[]>([]);

    const showToast = useCallback((tone: ToastTone, message: string) => {
        const id = crypto.randomUUID();
        setToasts((prev) => [...prev, { id, tone, message }]);
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 5000);
    }, []);

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}

            <div
                aria-live="polite"
                role="status"
                className="fixed bottom-4 right-4 z-50 flex flex-col gap-2"
            >
                {toasts.map((toast) => (
                    <div
                        key={toast.id}
                        className={[
                            "rounded-md px-4 py-3 text-sm font-medium shadow-lg",
                            toneClasses[toast.tone],
                        ].join(" ")}
                    >
                        {toast.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast(): ToastContextValue {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error("useToast debe usarse dentro de un <ToastProvider>");
    }
    return context;
}
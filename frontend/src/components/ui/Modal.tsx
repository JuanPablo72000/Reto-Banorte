import { ReactNode, useEffect, useRef } from "react";

export interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    title: string;
    children: ReactNode;
    footer?: ReactNode;
}

const FOCUSABLE_SELECTOR =
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function Modal({ isOpen, onClose, title, children, footer }: ModalProps) {
    const dialogRef = useRef<HTMLDivElement>(null);
    const previouslyFocused = useRef<HTMLElement | null>(null);

    useEffect(() => {
        if (!isOpen) return;

        previouslyFocused.current = document.activeElement as HTMLElement;
        document.body.style.overflow = "hidden";

        const dialogNode = dialogRef.current;
        const focusableEls = dialogNode?.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
        focusableEls?.[0]?.focus();

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                onClose();
                return;
            }

            if (e.key === "Tab" && focusableEls && focusableEls.length > 0) {
                const first = focusableEls[0];
                const last = focusableEls[focusableEls.length - 1];

                if (e.shiftKey && document.activeElement === first) {
                    e.preventDefault();
                    last.focus();
                } else if (!e.shiftKey && document.activeElement === last) {
                    e.preventDefault();
                    first.focus();
                }
            }
        };

        document.addEventListener("keydown", handleKeyDown);

        return () => {
            document.removeEventListener("keydown", handleKeyDown);
            document.body.style.overflow = "";
            previouslyFocused.current?.focus();
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
                aria-hidden="true"
                onClick={onClose}
                className="absolute inset-0 bg-black/50"
            />

            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="modal-title"
                className="relative w-full max-w-md rounded-lg bg-[var(--color-surface)] p-6 shadow-xl"
            >
                <h2 id="modal-title" className="text-lg font-semibold text-[var(--color-text)]">
                    {title}
                </h2>

                <div className="mt-4 text-sm text-[var(--color-text)]">{children}</div>

                {footer && <div className="mt-6 flex justify-end gap-3">{footer}</div>}
            </div>
        </div>
    );
}
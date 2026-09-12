import { KeyboardEvent, ReactNode, useEffect, useId, useRef, useState } from "react";

export interface DropdownItem {
    id: string;
    label: string;
    onSelect: () => void;
    danger?: boolean;
}

export interface DropdownProps {
    trigger: ReactNode;
    items: DropdownItem[];
}

export function Dropdown({ trigger, items }: DropdownProps) {
    const [open, setOpen] = useState(false);
    const [activeIndex, setActiveIndex] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);
    const menuId = useId();

    useEffect(() => {
        if (!open) return;

        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [open]);

    const handleTriggerKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen(true);
            setActiveIndex(0);
        }
    };

    const handleMenuKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
        if (e.key === "Escape") {
            setOpen(false);
            return;
        }
        if (e.key === "ArrowDown") {
            e.preventDefault();
            setActiveIndex((i) => (i + 1) % items.length);
        }
        if (e.key === "ArrowUp") {
            e.preventDefault();
            setActiveIndex((i) => (i - 1 + items.length) % items.length);
        }
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            items[activeIndex]?.onSelect();
            setOpen(false);
        }
    };

    return (
        <div className="relative inline-block" ref={containerRef}>
            <div
                role="button"
                tabIndex={0}
                aria-haspopup="menu"
                aria-expanded={open}
                aria-controls={menuId}
                onClick={() => setOpen((o) => !o)}
                onKeyDown={handleTriggerKeyDown}
            >
                {trigger}
            </div>

            {open && (
                <div
                    id={menuId}
                    role="menu"
                    onKeyDown={handleMenuKeyDown}
                    className={[
                        "absolute left-0 z-20 mt-2 min-w-[180px] rounded-md border py-1 shadow-lg",
                        "border-[var(--color-border)] bg-[var(--color-surface)]",
                    ].join(" ")}
                >
                    {items.map((item, index) => (
                        <button
                            key={item.id}
                            role="menuitem"
                            type="button"
                            tabIndex={-1}
                            onClick={() => {
                                item.onSelect();
                                setOpen(false);
                            }}
                            onMouseEnter={() => setActiveIndex(index)}
                            className={[
                                "block w-full px-4 py-2 text-left text-sm",
                                item.danger ? "text-[var(--color-danger)]" : "text-[var(--color-text)]",
                                index === activeIndex ? "bg-[var(--color-surface-2)]" : "",
                            ].join(" ")}
                        >
                            {item.label}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
import { KeyboardEvent, ReactNode, useId, useState } from "react";

export interface TabItem {
    id: string;
    label: string;
    content: ReactNode;
}

export interface TabsProps {
    items: TabItem[];
    defaultTabId?: string;
    onChange?: (id: string) => void;
}

export function Tabs({ items, defaultTabId, onChange }: TabsProps) {
    const baseId = useId();
    const [activeId, setActiveId] = useState(defaultTabId ?? items[0]?.id);

    const selectTab = (id: string) => {
        setActiveId(id);
        onChange?.(id);
    };

    const handleKeyDown = (e: KeyboardEvent<HTMLButtonElement>, index: number) => {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        e.preventDefault();
        const direction = e.key === "ArrowRight" ? 1 : -1;
        const nextIndex = (index + direction + items.length) % items.length;
        const nextTab = items[nextIndex];
        selectTab(nextTab.id);
        document.getElementById(`${baseId}-tab-${nextTab.id}`)?.focus();
    };

    const activeItem = items.find((item) => item.id === activeId);

    return (
        <div>
            <div role="tablist" aria-label="Tabs" className="flex gap-1 border-b border-[var(--color-border)]">
                {items.map((item, index) => {
                    const selected = item.id === activeId;
                    return (
                        <button
                            key={item.id}
                            id={`${baseId}-tab-${item.id}`}
                            role="tab"
                            type="button"
                            aria-selected={selected}
                            aria-controls={`${baseId}-panel-${item.id}`}
                            tabIndex={selected ? 0 : -1}
                            onClick={() => selectTab(item.id)}
                            onKeyDown={(e) => handleKeyDown(e, index)}
                            className={[
                                "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
                                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                                selected
                                    ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                                    : "border-transparent text-[var(--color-text-muted)] hover:text-[var(--color-text)]",
                            ].join(" ")}
                        >
                            {item.label}
                        </button>
                    );
                })}
            </div>

            {items.map((item) => (
                <div
                    key={item.id}
                    id={`${baseId}-panel-${item.id}`}
                    role="tabpanel"
                    aria-labelledby={`${baseId}-tab-${item.id}`}
                    hidden={item.id !== activeId}
                    className="pt-4"
                >
                    {item.id === activeId ? item.content : null}
                </div>
            ))}
        </div>
    );
}
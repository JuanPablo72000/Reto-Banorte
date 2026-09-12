import { ReactNode, useId, useState } from "react";

export interface AccordionItem {
    id: string;
    title: string;
    content: ReactNode;
}

export interface AccordionProps {
    items: AccordionItem[];
    allowMultiple?: boolean;
    defaultOpenIds?: string[];
}

export function Accordion({ items, allowMultiple = false, defaultOpenIds = [] }: AccordionProps) {
    const baseId = useId();
    const [openIds, setOpenIds] = useState<string[]>(defaultOpenIds);

    const toggle = (id: string) => {
        setOpenIds((prev) => {
            const isOpen = prev.includes(id);
            if (allowMultiple) {
                return isOpen ? prev.filter((x) => x !== id) : [...prev, id];
            }
            return isOpen ? [] : [id];
        });
    };

    return (
        <div className="divide-y divide-[var(--color-border)] border-y border-[var(--color-border)]">
            {items.map((item) => {
                const isOpen = openIds.includes(item.id);
                return (
                    <div key={item.id}>
                        <h3>
                            <button
                                type="button"
                                id={`${baseId}-header-${item.id}`}
                                aria-expanded={isOpen}
                                aria-controls={`${baseId}-panel-${item.id}`}
                                onClick={() => toggle(item.id)}
                                className={[
                                    "flex w-full items-center justify-between gap-2 py-3 text-left text-sm font-medium",
                                    "text-[var(--color-text)]",
                                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)]",
                                ].join(" ")}
                            >
                                {item.title}
                                <span
                                    aria-hidden="true"
                                    className={["transition-transform motion-reduce:transition-none", isOpen ? "rotate-180" : ""].join(" ")}
                                >
                  ▾
                </span>
                            </button>
                        </h3>
                        <div
                            id={`${baseId}-panel-${item.id}`}
                            role="region"
                            aria-labelledby={`${baseId}-header-${item.id}`}
                            hidden={!isOpen}
                            className="pb-3 text-sm text-[var(--color-text)]"
                        >
                            {item.content}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
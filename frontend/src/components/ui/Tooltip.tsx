import { ReactNode, useId, useState } from "react";

export interface TooltipProps {
    content: string;
    children: ReactNode;
    position?: "top" | "bottom";
}

const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
};

export function Tooltip({ content, children, position = "top" }: TooltipProps) {
    const [visible, setVisible] = useState(false);
    const tooltipId = useId();

    const show = () => setVisible(true);
    const hide = () => setVisible(false);

    return (
        <span
            className="relative inline-flex"
            onMouseEnter={show}
            onMouseLeave={hide}
            onFocus={show}
            onBlur={hide}
        >
      <span aria-describedby={visible ? tooltipId : undefined} className="inline-flex">
        {children}
      </span>

            {visible && (
                <span
                    id={tooltipId}
                    role="tooltip"
                    className={[
                        "absolute z-10 whitespace-nowrap rounded-md px-2.5 py-1.5 text-xs font-medium",
                        "bg-[var(--color-text)] text-[var(--color-bg)] shadow-md",
                        positionClasses[position],
                    ].join(" ")}
                >
          {content}
        </span>
            )}
    </span>
    );
}
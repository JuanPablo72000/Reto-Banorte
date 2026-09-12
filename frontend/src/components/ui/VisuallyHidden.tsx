import { ElementType, HTMLAttributes, ReactNode } from "react";

export interface VisuallyHiddenProps extends HTMLAttributes<HTMLElement> {
    children: ReactNode;
    as?: ElementType;
}

export function VisuallyHidden({ children, as: Component = "span", className = "", ...props }: VisuallyHiddenProps) {
    return (
        <Component className={["sr-only", className].join(" ")} {...props}>
            {children}
        </Component>
    );
}
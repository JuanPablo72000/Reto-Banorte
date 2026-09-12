import { AnchorHTMLAttributes } from "react";

export interface SkipLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
    targetId?: string;
}

export function SkipLink({ targetId = "main-content", children, className = "", ...props }: SkipLinkProps) {
    return (
        <a href={`#${targetId}`} className={["skip-link", className].join(" ")} {...props}>
            {children ?? "Saltar al contenido principal"}
        </a>
    );
}
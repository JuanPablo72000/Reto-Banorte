import { HTMLAttributes } from "react";

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
    name: string;
    src?: string;
    size?: "sm" | "md" | "lg";
}

const sizeClasses = {
    sm: "h-8 w-8 text-xs",
    md: "h-10 w-10 text-sm",
    lg: "h-14 w-14 text-lg",
};

function getInitials(name: string): string {
    const parts = name.trim().split(/\s+/);
    const initials = parts.slice(0, 2).map((p) => p[0]?.toUpperCase() ?? "");
    return initials.join("") || "?";
}

export function Avatar({ name, src, size = "md", className = "", ...props }: AvatarProps) {
    return (
        <div
            role="img"
            aria-label={name}
            className={[
                "flex shrink-0 items-center justify-center overflow-hidden rounded-full",
                "bg-[var(--color-surface-3)] font-medium text-[var(--color-text)]",
                sizeClasses[size],
                className,
            ].join(" ")}
            {...props}
        >
            {src ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={src} alt="" className="h-full w-full object-cover" />
            ) : (
                <span aria-hidden="true">{getInitials(name)}</span>
            )}
        </div>
    );
}
"use client";

import { ReactNode } from "react";
import { ThemeToggle } from "@/components/accessibility/ThemeToggle";
import { ContrastToggle } from "@/components/accessibility/ContrastToggle";
import { FontScaleControl } from "@/components/accessibility/FontScaleControl";
import { SkipLink } from "@/components/ui/SkipLink";

export interface AppShellProps {
    children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
    return (
        <div className="flex h-screen flex-col bg-[var(--color-surface)]">
            <SkipLink href="#main-content" />

            <header className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3">
                <span className="text-lg font-semibold text-[var(--color-text)]">
                    Banca Personal
                </span>

                <div className="flex items-center gap-3">
                    <FontScaleControl />
                    <ContrastToggle />
                    <ThemeToggle />
                </div>
            </header>

            <main id="main-content" className="flex-1 overflow-hidden">
                {children}
            </main>
        </div>
    );
}
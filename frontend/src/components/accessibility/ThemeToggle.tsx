"use client";

import { IconButton } from "../ui/IconButton";
import { useA11y } from "./A11yProvider";

export function ThemeToggle() {
    const { theme, toggleTheme } = useA11y();
    const isDark = theme === "dark";

    return (
        <IconButton
            icon={isDark ? "☀️" : "🌙"}
            aria-label={isDark ? "Cambiar a tema claro" : "Cambiar a tema oscuro"}
            onClick={toggleTheme}
            variant="secondary"
        />
    );
}
"use client";

import { useA11y, Palette } from "./A11yProvider";

const PALETTE_LABELS: Record<Palette, string> = {
    normal: "Normal",
    colorblind: "Daltónica",
    mono: "Monocromática",
};

export function PaletteToggle() {
    const { palette, setPalette } = useA11y();

    return (
        <label className="flex items-center gap-2 text-sm text-[var(--color-text)]">
            <span className="sr-only">Paleta de color</span>
            <select
                value={palette}
                onChange={(e) => setPalette(e.target.value as Palette)}
                className="rounded border border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1"
                aria-label="Seleccionar paleta de color"
            >
                {(Object.entries(PALETTE_LABELS) as [Palette, string][]).map(([value, label]) => (
                    <option key={value} value={value}>
                        {label}
                    </option>
                ))}
            </select>
        </label>
    );
}
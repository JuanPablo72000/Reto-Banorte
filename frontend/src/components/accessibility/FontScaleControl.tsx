"use client";

import { IconButton } from "../ui/IconButton";
import { useA11y } from "./A11yProvider";

const MIN_SCALE = 0.85;
const MAX_SCALE = 1.5;
const STEP = 0.15;

export function FontScaleControl() {
    const { fontScale, setFontScale } = useA11y();

    const decrease = () => setFontScale(Math.max(MIN_SCALE, Number((fontScale - STEP).toFixed(2))));
    const increase = () => setFontScale(Math.min(MAX_SCALE, Number((fontScale + STEP).toFixed(2))));

    return (
        <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-[var(--color-text)]">Tamaño de letra</span>

            <div className="flex items-center gap-1">
                <IconButton
                    icon="A-"
                    aria-label="Reducir tamaño de letra"
                    onClick={decrease}
                    disabled={fontScale <= MIN_SCALE}
                    variant="secondary"
                    size="sm"
                />

                <span
                    role="status"
                    aria-live="polite"
                    className="min-w-[48px] text-center text-sm text-[var(--color-text-muted)]"
                >
          {Math.round(fontScale * 100)}%
        </span>

                <IconButton
                    icon="A+"
                    aria-label="Aumentar tamaño de letra"
                    onClick={increase}
                    disabled={fontScale >= MAX_SCALE}
                    variant="secondary"
                    size="sm"
                />
            </div>
        </div>
    );
}
"use client";

import { Switch } from "../ui/Switch";
import { useA11y } from "./A11yProvider";

export function ContrastToggle() {
    const { contrast, toggleContrast } = useA11y();

    return (
        <Switch
            label="Alto contraste"
            hint="Aumenta el contraste de texto y bordes para mejorar la legibilidad"
            checked={contrast === "high"}
            onCheckedChange={toggleContrast}
        />
    );
}
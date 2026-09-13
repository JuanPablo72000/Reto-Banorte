import { Icon } from "@/components/ui/Icon";

// Aviso de que los datos mostrados son del backend (no demo) o de
// demostración (backend apagado / modo demo).
export function DemoBadge({ activo = true }: { activo?: boolean }) {
    if (!activo) return null;
    return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--color-warning-bg)] px-2.5 py-1 text-xs font-medium text-[var(--color-warning-text)]">
            <Icon name="info" size={14} />
            Datos de demostración
        </span>
    );
}

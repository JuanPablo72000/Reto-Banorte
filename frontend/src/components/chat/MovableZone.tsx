"use client";
/* eslint-disable react-hooks/refs -- Falso positivo: aquí NO se lee
   `.current` en render; se pasan objetos ref como prop `ref` y se lee
   estado (ordered/grabbedId). El acceso real a .current vive solo en
   handlers/eventos dentro de useMovable. */
import type { ReactNode } from "react";
import { useMovable } from "@/components/chat/useMovable";
import type { MovableHandleProps } from "@/components/chat/useMovable";

export interface MovableZoneContext {
  grabbed: boolean;
  dragging: boolean;
  position: number;
  total: number;
  handleProps: MovableHandleProps;
  handleAriaLabel: string;
}
export interface MovableZoneProps<T extends { id: string }> {
  items: readonly T[];
  storageKey: string;
  label: string;
  orientation?: "horizontal" | "vertical";
  etiquetaItem?: string;
  className?: string;
  children: (item: T, index: number, ctx: MovableZoneContext) => ReactNode;
}

/** Zona reordenable genérica (tarjetas del plan, pills de sugerencias). Renderiza <ul> + live region. */
export function MovableZone<T extends { id: string }>({
  items, storageKey, label, orientation = "vertical", etiquetaItem, className, children,
}: MovableZoneProps<T>) {
  const m = useMovable<T>({ items, storageKey, orientation, etiquetaItem });
  return (
    <>
      <ul ref={m.containerRef} role="list" aria-label={label}
        className={`flex ${orientation === "horizontal" ? "flex-row" : "flex-col"} gap-[var(--gap-stack)] p-0 m-0 list-none ${className ?? ""}`}>
        {m.ordered.map((item, index) => {
          const grabbed = m.grabbedId === item.id;
          const ctx: MovableZoneContext = {
            grabbed,
            dragging: m.draggingId === item.id,
            position: index + 1,
            total: m.ordered.length,
            handleProps: m.handleProps(item.id),
            handleAriaLabel: `Reordenar ${etiquetaItem ?? "elemento"}: posición ${index + 1} de ${m.ordered.length}. Enter para tomar, flechas para mover, Enter para soltar.`,
          };
          return (
            <li key={item.id} ref={m.itemRef(item.id)} data-movable-item data-grabbed={grabbed || undefined}
              className={`relative ${ctx.dragging ? "z-10 shadow-[var(--shadow-2)] rounded-xl motion-reduce:shadow-[var(--shadow-1)]" : ""} ${grabbed ? "outline outline-2 outline-[var(--color-accent)] rounded-xl" : ""}`}>
              {children(item, index, ctx)}
            </li>
          );
        })}
      </ul>
      <p id={m.liveId} role="status" aria-live="polite" className="sr-only">{m.liveMessage}</p>
    </>
  );
}
// WCAG 2.2 AA: lista semántica role="list" (1.3.1); grip dedicado evita conflictos con el control principal
// (2.5.8 target ≥44px lo pone el consumidor del ctx); estado grabbed visible con outline accent (1.4.11, 2.4.7);
// live region polite separada del contenido (4.1.3); sin animación de arrastre si reduced-motion (CSS global).
// Prueba lector: 1) Flechas de navegación listan los items en el orden actual. 2) Tras mover con teclado, el
// anuncio confirma posición nueva. 3) Recarga la página: el orden persistido se anuncia igual (localStorage).
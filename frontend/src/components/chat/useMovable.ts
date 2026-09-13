// path: components/chat/useMovable.ts
"use client";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import type { KeyboardEvent as RKeyboardEvent, PointerEvent as RPointerEvent, RefObject } from "react";

export interface MovableHandleProps {
  onPointerDown: (e: RPointerEvent<HTMLButtonElement>) => void;
  onPointerMove: (e: RPointerEvent<HTMLButtonElement>) => void;
  onPointerUp: (e: RPointerEvent<HTMLButtonElement>) => void;
  onPointerCancel: (e: RPointerEvent<HTMLButtonElement>) => void;
  onKeyDown: (e: RKeyboardEvent<HTMLButtonElement>) => void;
}
export interface UseMovableOptions<T extends { id: string }> {
  items: readonly T[];
  storageKey: string;
  orientation?: "horizontal" | "vertical";
  etiquetaItem?: string;
}
export interface UseMovableResult<T extends { id: string }> {
  ordered: readonly T[];
  grabbedId: string | null;
  draggingId: string | null;
  liveMessage: string;
  liveId: string;
  containerRef: RefObject<HTMLUListElement | null>;
  itemRef: (id: string) => (el: HTMLLIElement | null) => void;
  handleProps: (id: string) => MovableHandleProps;
}

function leerOrden(storageKey: string, ids: readonly string[]): string[] {
  if (typeof window === "undefined") return [...ids];
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return [...ids];
    const guardado: unknown = JSON.parse(raw);
    if (!Array.isArray(guardado)) return [...ids];
    const validos = guardado.filter((x): x is string => typeof x === "string" && ids.includes(x));
    const sinDuplicados = [...new Set(validos)];
    return [...sinDuplicados, ...ids.filter((id) => !sinDuplicados.includes(id))];
  } catch { return [...ids]; }
}
function mover<T>(arr: readonly T[], de: number, a: number): T[] {
  const copia = [...arr]; const [x] = copia.splice(de, 1); copia.splice(a, 0, x); return copia;
}

/** Reordenado con Pointer Events + teclado, persistido en localStorage. Sin dependencias. */
export function useMovable<T extends { id: string }>({ items, storageKey, orientation = "vertical", etiquetaItem = "Elemento" }: UseMovableOptions<T>): UseMovableResult<T> {
  const ids = useMemo(() => items.map((i) => i.id), [items]);
  const [order, setOrder] = useState<string[]>(() => leerOrden(storageKey, ids));
  const [grabbedId, setGrabbedId] = useState<string | null>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [liveMessage, setLiveMessage] = useState("");
  const liveId = useId();
  const containerRef = useRef<HTMLUListElement | null>(null);
  const refs = useRef(new Map<string, HTMLLIElement>());
  const drag = useRef<{ id: string; x: number; y: number; moved: boolean } | null>(null);

  useEffect(() => {  // reconcilia si la IA manda items nuevos
    // Reconciliación guardada: si el orden ya coincide se regresa `prev`
    // idéntico y React omite el re-render (sin cascadas). Necesario porque
    // el orden del usuario debe sobrevivir a planes nuevos sin perder su
    // arreglo.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOrder((prev) => {
      const ok = prev.filter((id) => ids.includes(id));
      const next = [...ok, ...ids.filter((id) => !ok.includes(id))];
      return next.length === prev.length && next.every((v, i) => v === prev[i]) ? prev : next;
    });
  }, [ids]);
  useEffect(() => {
    try { window.localStorage.setItem(storageKey, JSON.stringify(order)); } catch { /* privado/incognito */ }
  }, [order, storageKey]);

  const itemRef = useCallback((id: string) => (el: HTMLLIElement | null) => {
    if (el) refs.current.set(id, el); else refs.current.delete(id);
  }, []);

  const indicePuntero = useCallback((clientX: number, clientY: number): number => {
    const rects = [...refs.current.values()].map((el) => el.getBoundingClientRect());
    if (rects.length === 0) return -1;
    const horizontal = orientation === "horizontal";
    let idx = 0;
    rects.forEach((r, i) => {
      const medio = horizontal ? r.left + r.width / 2 : r.top + r.height / 2;
      const pos = horizontal ? clientX : clientY;
      if (pos > medio) idx = i + 1 > rects.length - 1 ? rects.length - 1 : i + 1;
    });
    return Math.min(idx, rects.length - 1);
  }, [orientation]);

  const ordered = useMemo(() => {
    const porId = new Map(items.map((i) => [i.id, i] as const));
    return order.map((id) => porId.get(id)).filter((x): x is T => x !== undefined);
  }, [order, items]);

  const anunciar = useCallback((id: string, nextOrder: readonly string[]) => {
    const n = nextOrder.indexOf(id) + 1;
    setLiveMessage(`${etiquetaItem} movido a posición ${n} de ${nextOrder.length}`);
  }, [etiquetaItem]);

  const handleProps = useCallback((id: string): MovableHandleProps => ({
    onPointerDown: (e) => {
      if (e.button !== 0) return;
      e.currentTarget.setPointerCapture(e.pointerId);
      drag.current = { id, x: e.clientX, y: e.clientY, moved: false };
      setDraggingId(id);
    },
    onPointerMove: (e) => {
      const d = drag.current;
      if (!d || d.id !== id) return;
      if (!d.moved && Math.hypot(e.clientX - d.x, e.clientY - d.y) < 6) return; // umbral: clic no es drag
      d.moved = true;
      setOrder((prev) => {
        const actual = prev.indexOf(id);
        const objetivo = indicePuntero(e.clientX, e.clientY);
        if (objetivo < 0 || objetivo === actual) return prev;
        return mover(prev, actual, objetivo);
      });
    },
    onPointerUp: (e) => {
      const d = drag.current;
      if (d && d.id === id) {
        if (d.moved) {
          setOrder((prev) => { anunciar(id, prev); return prev; });
        }
      }
      if (e.currentTarget.hasPointerCapture(e.pointerId)) e.currentTarget.releasePointerCapture(e.pointerId);
      drag.current = null; setDraggingId(null);
    },
    onPointerCancel: () => { drag.current = null; setDraggingId(null); },
    onKeyDown: (e) => {
      const clave = e.key;
      const aceptadas = ["Enter", " ", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End", "Escape"];
      if (!aceptadas.includes(clave)) return;
      e.preventDefault(); e.stopPropagation();
      if (clave === "Enter" || clave === " ") {
        if (grabbedId === id) {
          setGrabbedId(null);
          setOrder((prev) => { anunciar(id, prev); return prev; });
        } else {
          setGrabbedId(id);
          setLiveMessage(`${etiquetaItem} tomado. Use flechas para mover, Enter para soltar, Escape para cancelar.`);
        }
        return;
      }
      if (clave === "Escape") { setGrabbedId(null); setLiveMessage("Movimiento cancelado"); return; }
      if (grabbedId !== id) return;
      setOrder((prev) => {
        const actual = prev.indexOf(id);
        let objetivo = actual;
        if (clave === "ArrowUp" || clave === "ArrowLeft") objetivo = Math.max(0, actual - 1);
        if (clave === "ArrowDown" || clave === "ArrowRight") objetivo = Math.min(prev.length - 1, actual + 1);
        if (clave === "Home") objetivo = 0;
        if (clave === "End") objetivo = prev.length - 1;
        if (objetivo === actual) return prev;
        const next = mover(prev, actual, objetivo);
        anunciar(id, next);
        return next;
      });
    },
  }), [grabbedId, anunciar, etiquetaItem, indicePuntero]);

  return { ordered, grabbedId, draggingId, liveMessage, liveId, containerRef, itemRef, handleProps };
}
// WCAG 2.2 AA: operable por teclado (2.1.1) con Enter/Espacio=tomar/soltar, flechas/Home/End mueven, Escape
// cancela; aria-grabbed refleja estado (4.1.2); live region role="status" anuncia "movido a posición N" (3.3.1,
// 4.1.3); pointer capture sin librerías (2.5.1 umbral 6px evita drag accidental); orden persistido => preferencias
// conservadas. Reduced-motion: el hook no anima; CSS anula transiciones de arrastre.
// Prueba lector: 1) Tab hasta el grip: NVDA anuncia "Reordenar, posición X de Y, botón". 2) Enter + ArrowDown:
// anuncia "movido a posición N". 3) Enter suelta y el foco permanece en el grip tras el reorder.
"use client";
import { useEffect, useId, useRef, useState } from "react";
import type { FormEvent } from "react";
import { attrsAnimacion } from "@/lib/atributos";

export interface CampoStep {
  id: string; etiqueta: string;
  tipo: "texto" | "email" | "numero" | "select";
  opciones?: readonly { valor: string; etiqueta: string }[];
  requerido?: boolean; hint?: string; placeholder?: string;
}
export interface PasoStep { id: string; titulo: string; descripcion?: string; campos: readonly CampoStep[] }
export interface MensajesValidacion { requerido: string; email: string; numero: string }
export interface StepperFormProps {
    tituloForm: string;
    pasos: readonly PasoStep[];
    onSubmit: (valores: Record<string, string>) => void;
    mensajes?: Partial<MensajesValidacion>;
    animation?: string | null;
    orden?: number;
}
const MSG: MensajesValidacion = { requerido: "Este campo es obligatorio.", email: "Capture un correo válido.", numero: "Capture una cantidad válida." };

export function StepperForm({ tituloForm, pasos, onSubmit, mensajes, animation = "fade" }: StepperFormProps) {
  const uid = useId();
  const msgs = { ...MSG, ...mensajes };
  const [idx, setIdx] = useState(0);
  const [valores, setValores] = useState<Record<string, string>>({});
  const [errores, setErrores] = useState<Record<string, string>>({});
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  const primero = useRef(true);
  const attrs = attrsAnimacion(animation, undefined);
  const paso = pasos[idx];

  useEffect(() => { if (primero.current) { primero.current = false; return; } headingRef.current?.focus(); }, [idx]);

  function validar(p: PasoStep, v: Record<string, string>): Record<string, string> {
    const e: Record<string, string> = {};
    for (const c of p.campos) {
      const val = (v[c.id] ?? "").trim();
      if (c.requerido && val === "") e[c.id] = msgs.requerido;
      else if (val !== "" && c.tipo === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) e[c.id] = msgs.email;
      else if (val !== "" && c.tipo === "numero" && !Number.isFinite(Number(val.replace(",", ".")))) e[c.id] = msgs.numero;
    }
    return e;
  }
  function avanzar(e: FormEvent) {
    e.preventDefault();
    const errs = validar(paso, valores);
    setErrores(errs);
    if (Object.keys(errs).length > 0) {
      const primer = paso.campos.find((c) => errs[c.id]);
      if (primer) document.getElementById(`${uid}-c-${primer.id}`)?.focus();
      return;
    }
    if (idx < pasos.length - 1) setIdx(idx + 1);
    else onSubmit(valores);
  }

  if (!paso) return null;
  return (
    <form onSubmit={avanzar} aria-labelledby={`${uid}-titulo`} noValidate {...attrs}
      className="rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-2)] p-[var(--pad-card)] shadow-[var(--shadow-1)]">
      <h3 id={`${uid}-titulo`} className="text-[var(--text-titulo)] font-semibold text-[var(--color-text)]">{tituloForm}</h3>
      <ol aria-label="Progreso del formulario" className="mt-2 flex flex-wrap gap-[var(--gap-item)] text-sm">
        {pasos.map((p, i) => (
          <li key={p.id} aria-current={i === idx ? "step" : undefined}
            className={`rounded-full px-3 py-1 ${i === idx ? "bg-[var(--color-accent)] text-[var(--color-accent-text)] font-semibold" : i < idx ? "bg-[var(--color-success-bg)] text-[var(--color-success-text)]" : "bg-[var(--color-surface-3)] text-[var(--color-text-muted)]"}`}>
            <span aria-hidden="true">{i + 1}.</span> {p.titulo}
            <span className="sr-only">{i === idx ? ` (paso actual, ${i + 1} de ${pasos.length})` : i < idx ? " (completado)" : ""}</span>
          </li>
        ))}
      </ol>
      <p role="status" className="sr-only">Paso {idx + 1} de {pasos.length}: {paso.titulo}</p>
      <fieldset className="mt-4 border-0 p-0 m-0">
        <legend className="sr-only">{paso.titulo}</legend>
        <h4 ref={headingRef} tabIndex={-1} className="text-[var(--text-body)] font-semibold text-[var(--color-text)] focus:outline-none">{paso.titulo}</h4>
        {paso.descripcion && <p className="mt-1 text-[var(--color-text-muted)]">{paso.descripcion}</p>}
        <div className="mt-3 flex flex-col gap-[var(--gap-stack)]">
          {paso.campos.map((c) => {
            const errId = `${uid}-e-${c.id}`; const hintId = `${uid}-h-${c.id}`;
            const desc = [c.hint ? hintId : null, errores[c.id] ? errId : null].filter(Boolean).join(" ") || undefined;
            const comun = {
              id: `${uid}-c-${c.id}`, "aria-invalid": errores[c.id] ? true as const : undefined, "aria-describedby": desc,
              "aria-required": c.requerido ? true as const : undefined,
              value: valores[c.id] ?? "",
              onChange: (ev: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setValores((v) => ({ ...v, [c.id]: ev.target.value })),
              className: `min-h-[var(--target-min)] w-full rounded-lg border bg-[var(--color-surface)] px-3 text-[var(--text-body)] text-[var(--color-text)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] ${errores[c.id] ? "border-[var(--color-danger-text)]" : "border-[var(--color-border)]"}`,
            };
            return (
              <div key={c.id}>
                <label htmlFor={`${uid}-c-${c.id}`} className="mb-1 block font-medium text-[var(--color-text)]">
                  {c.etiqueta}{c.requerido && <span aria-hidden="true"> *</span>}
                </label>
                {c.tipo === "select" ? (
                  <select {...comun}>
                    <option value="">Seleccione…</option>
                    {(c.opciones ?? []).map((o) => <option key={o.valor} value={o.valor}>{o.etiqueta}</option>)}
                  </select>
                ) : (
                  <input {...comun} type={c.tipo === "numero" ? "text" : c.tipo}
                    inputMode={c.tipo === "numero" ? "decimal" : c.tipo === "email" ? "email" : undefined}
                    placeholder={c.placeholder} />
                )}
                {c.hint && <p id={hintId} className="mt-1 text-sm text-[var(--color-text-muted)]">{c.hint}</p>}
                {errores[c.id] && <p id={errId} role="alert" className="mt-1 text-sm font-medium text-[var(--color-danger-text)]">{errores[c.id]}</p>}
              </div>
            );
          })}
        </div>
      </fieldset>
      <div className="mt-4 flex gap-[var(--gap-item)]">
        <button type="button" disabled={idx === 0} onClick={() => setIdx((i) => Math.max(0, i - 1))}
          className="min-h-[var(--target-min)] rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)] px-5 font-medium text-[var(--color-text)] hover:bg-[var(--color-surface-3)] active:scale-[0.98] motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] disabled:opacity-50">
          Regresar
        </button>
        <button type="submit"
          className="min-h-[var(--target-min)] rounded-full bg-[var(--color-accent)] px-6 font-semibold text-[var(--color-accent-text)] hover:bg-[var(--color-accent-hover)] active:scale-[0.98] motion-reduce:active:scale-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--color-accent)] focus-visible:outline-offset-2">
          {idx < pasos.length - 1 ? "Siguiente" : "Confirmar"}
        </button>
      </div>
    </form>
  );
}
// WCAG 2.2 AA: fieldset/legend + label htmlFor (1.3.1, 3.3.2); errores inline role="alert" + aria-describedby +
// aria-invalid y foco al primer error (3.3.1, 3.3.3); ol con aria-current="step" y status "Paso N de M" (4.1.3);
// foco al encabezado del paso al cambiar (2.4.3); targets ≥44px (2.5.8); validación sin depender de color (texto).
// Prueba lector: 1) Tab: anuncia paso actual y campos con requerido/hint. 2) Submit inválido: alerta inline y foco
// en el campo. 3) Siguiente: anuncia "Paso N de M: título" al mover el foco al encabezado.
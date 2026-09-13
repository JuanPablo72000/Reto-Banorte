import { NextRequest, NextResponse } from "next/server";
import { ejecutarAccion } from "@/lib/mcp/client";

// Borra la memoria del asistente (user_memory.json del MCP) para un usuario.
// No llama a la IA: es una acción de mantenimiento del puente (run_turn.py).
export async function POST(req: NextRequest) {
    let idUser = 1;
    try {
        const body = (await req.json()) as { id_user?: number };
        if (typeof body.id_user === "number") idUser = body.id_user;
    } catch {
        // body vacío: se usa el usuario demo (id 1)
    }
    const res = await ejecutarAccion("reset_memoria", idUser);
    if (res.error) {
        return NextResponse.json({ ok: false, error: res.error }, { status: 502 });
    }
    return NextResponse.json({ ok: true });
}

import { NextRequest, NextResponse } from "next/server";
import { ejecutarTurno } from "@/lib/mcp/client";
import type { ChatContext } from "@/lib/types/action-plan";

export const maxDuration = 300;

interface ChatBody {
    mensaje?: string;
    contexto?: ChatContext;
}

export async function POST(req: NextRequest) {
    let body: ChatBody;
    try {
        body = (await req.json()) as ChatBody;
    } catch {
        return NextResponse.json({ error: "body no es JSON válido" }, { status: 400 });
    }
    const mensaje = (body.mensaje ?? "").trim();
    if (!mensaje) {
        return NextResponse.json({ error: "falta 'mensaje'" }, { status: 400 });
    }
    const plan = await ejecutarTurno(mensaje, body.contexto ?? {});
    const status = plan.error ? 502 : 200;
    return NextResponse.json(plan, { status });
}

// Cliente del puente MCP — SOLO importable desde el servidor (usa
// child_process; únicamente lo usa app/api/chat/route.ts).
// Abstrae el transporte (hoy subproceso stdio vía run_turn.py; migrar a
// HTTP sin tocar el renderer: cambiar solo ejecutarTurno).
// Ver docs/frontend/07-puente-mcp-frontend.md.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import type { ActionPlanUI, ChatContext } from "@/lib/types/action-plan";

function resolverMcpDir(): string {
    if (process.env.MCP_DIR) return process.env.MCP_DIR;
    // En la imagen docker, mcp/ se copia a ./mcp-server; en dev local se
    // usa ../mcp (el repo). Se elige el primero que exista.
    for (const candidato of [
        path.resolve(process.cwd(), "mcp-server"),
        path.resolve(process.cwd(), "../mcp"),
    ]) {
        try {
            if (fs.existsSync(path.join(candidato, "run_turn.py"))) return candidato;
        } catch {
            // sigue al siguiente candidato
        }
    }
    return path.resolve(process.cwd(), "../mcp");
}

const MCP_DIR = resolverMcpDir();
const RUN_TURN = path.join(MCP_DIR, "run_turn.py");
const PYTHON = process.env.MCP_PYTHON ?? (process.platform === "win32" ? "python" : "python3");
const TIMEOUT_MS = Number(process.env.MCP_TIMEOUT_MS ?? 120000);

function entornoPuente(token?: string): NodeJS.ProcessEnv {
    const env: NodeJS.ProcessEnv = {
        ...process.env,
        PYTHONUNBUFFERED: "1",
    };
    if (token) env.BANORTE_API_TOKEN = token;
    return env;
}

function spawnPuente(pedido: object, token?: string): Promise<string> {
    return new Promise((resolve, reject) => {
        // Spawn intencional del puente MCP (no empaquetar): el script
        // vive fuera del bundle, en MCP_DIR/run_turn.py.
        const hijo = spawn(/*turbopackIgnore: true*/ PYTHON, [RUN_TURN], {
            cwd: MCP_DIR,
            env: entornoPuente(token),
        });
        let stdout = "";
        let stderr = "";
        const matar = setTimeout(() => hijo.kill("SIGKILL"), TIMEOUT_MS);
        hijo.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
        hijo.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
        hijo.on("error", (err) => reject(err));
        hijo.on("close", (codigo) => {
            clearTimeout(matar);
            if (codigo !== 0 && !stdout.trim()) {
                reject(new Error(`el puente terminó con exit=${codigo}: ${stderr.slice(-300)}`));
                return;
            }
            resolve(stdout);
        });
        hijo.stdin.write(JSON.stringify(pedido));
        hijo.stdin.end();
    });
}

export async function ejecutarTurno(
    mensaje: string,
    contexto: ChatContext = {},
): Promise<ActionPlanUI> {
    const { token, ...ctx } = contexto;
    const pedido = {
        mensaje,
        contexto: ctx,
        id_user: ctx.id_user ?? 1,
    };

    try {
        const stdout = await spawnPuente(pedido, token);
        return JSON.parse(stdout) as ActionPlanUI;
    } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return {
            error: msg.includes("no devolvió JSON")
                ? msg
                : `no se pudo ejecutar el MCP (${PYTHON} ${RUN_TURN}): ${msg}`,
        } as unknown as ActionPlanUI;
    }
}

/** Acciones de mantenimiento del puente que NO llaman a la IA
 *  (hoy: "reset_memoria" — borra la memoria del asistente del usuario). */
export async function ejecutarAccion(
    accion: string,
    idUser: number = 1,
    token?: string,
): Promise<{ ok?: boolean; error?: string }> {
    try {
        const stdout = await spawnPuente({ accion, id_user: idUser }, token);
        return JSON.parse(stdout) as { ok?: boolean; error?: string };
    } catch (e) {
        return { error: e instanceof Error ? e.message : String(e) };
    }
}

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

export async function ejecutarTurno(
    mensaje: string,
    contexto: ChatContext = {},
): Promise<ActionPlanUI> {
    const { token, ...ctx } = contexto;
    const pedido = JSON.stringify({
        mensaje,
        contexto: ctx,
        id_user: ctx.id_user ?? 1,
    });

    return new Promise((resolve) => {
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
        hijo.on("error", (err) =>
            resolve({
                error: `no se pudo lanzar el MCP (${PYTHON} ${RUN_TURN}): ${err.message}`,
            } as unknown as ActionPlanUI),
        );
        hijo.on("close", (codigo) => {
            clearTimeout(matar);
            try {
                resolve(JSON.parse(stdout) as ActionPlanUI);
            } catch {
                resolve({
                    error: `el MCP no devolvió JSON (exit=${codigo}): ${stderr.slice(-500) || stdout.slice(-500)}`,
                } as unknown as ActionPlanUI);
            }
        });
        hijo.stdin.write(pedido);
        hijo.stdin.end();
    });
}

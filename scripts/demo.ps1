<# Lanzador de la demo en Windows (sin make).
Uso:
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1                       # levanta todo y muestra el link
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -SoloEsperar           # solo espera y verifica (usado por `make demo`)
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Abajo                # apaga conservando la DB demo
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Reiniciar            # rebuild+recreate TODO y verifica
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Reiniciar frontend   # rebuild+recreate solo frontend
    powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Reiniciar mcp,frontend
#>
param([switch]$SoloEsperar, [switch]$Abajo, [switch]$Reiniciar, [string[]]$Servicios = @())

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Esperar-Url($url, $nombre, $intentos = 60) {
    for ($i = 1; $i -le $intentos; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing
            Write-Output "OK  $nombre -> $url ($($r.StatusCode))"
            return $true
        } catch {
            # Cualquier respuesta HTTP (incluso 4xx) = el puerto ya acepta.
            if ($_.Exception.Response) {
                Write-Output "OK  $nombre -> $url (responde)"
                return $true
            }
        }
        Start-Sleep -Seconds 5
    }
    Write-Output "FALLO $nombre no respondió en $url"
    return $false
}

if ($Abajo) {
    docker compose down
    exit 0
}

if ($Reiniciar) {
    # Reconstruye imágenes y recrea contenedores para tomar cambios de
    # código y del .env. Sin servicios = los 3 (api, mcp, frontend).
    # Ejemplos: -Reiniciar frontend | -Reiniciar mcp,frontend
    # NOTA: se pasa $lista SIN @splat a propósito (@lista parte strings
    # en caracteres cuando el script corre vía `powershell -File`).
    $lista = @($Servicios | Where-Object { $_ } | ForEach-Object { $_ -split '[,\s]+' } | Where-Object { $_ })
    Write-Output "Reiniciando con cambios: $(if ($lista.Count -gt 0) { $lista -join ', ' } else { 'todo' })"
    if ($lista.Count -gt 0) {
        docker compose up -d --build --force-recreate $lista
    } else {
        docker compose up -d --build --force-recreate
    }
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

if (-not $SoloEsperar -and -not $Reiniciar) {
    docker compose up --build -d
}

$ok = $true
$ok = (Esperar-Url "http://localhost:8000/health" "API") -and $ok
$ok = (Esperar-Url "http://localhost:3000/" "Frontend") -and $ok
# El MCP en modo http no tiene /health: basta con que el puerto acepte.
$ok = (Esperar-Url "http://localhost:8080/" "MCP") -and $ok

if ($ok) {
    Write-Output ""
    Write-Output "Listo para entrar -> http://localhost:3000 (chat)"
    Write-Output "API: http://localhost:8000/health | MCP: http://localhost:8080"
} else {
    Write-Output "Algo no levantó: últimos logs:"
    docker compose logs --tail 30
    Write-Output "Más detalle: 'docker compose logs <servicio>' o 'make demo-logs'"
    exit 1
}

# Genera el zip de entrega del proyecto final.
#   - Carpeta tirme-rrhh/ con los ficheros versionados en Git (sin venv, node_modules ni .env).
#   - La memoria (.docx y .pdf) en la raíz del zip.
# Uso (desde la raíz del repositorio):  powershell -ExecutionPolicy Bypass -File entrega\crear_zip.ps1
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$zip = Join-Path $PSScriptRoot 'Proyecto_Final_Ramon_Marquez.zip'
$memorias = @(
    (Join-Path $PSScriptRoot 'Memoria_Proyecto_Dashboard_RRHH_Ramon_Marquez.pdf'),
    (Join-Path $PSScriptRoot 'Memoria_Proyecto_Dashboard_RRHH_Ramon_Marquez.docx')
)

Push-Location $raiz
try {
    # git archive empaqueta el último commit: avisar si hay cambios sin confirmar
    $pendientes = git status --porcelain --untracked-files=no
    if ($pendientes) {
        Write-Warning "Hay cambios sin commit que NO irán en el zip:`n$($pendientes -join "`n")"
    }
    foreach ($m in $memorias) {
        if (-not (Test-Path $m)) { throw "Falta la memoria: $m" }
    }
    if (Test-Path $zip) { Remove-Item $zip }

    # La carpeta entrega/ se excluye con export-ignore en .gitattributes
    git archive --format=zip --prefix=tirme-rrhh/ -o $zip HEAD
    if ($LASTEXITCODE -ne 0) { throw 'git archive ha fallado' }

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archivo = [System.IO.Compression.ZipFile]::Open($zip, 'Update')
    try {
        foreach ($m in $memorias) {
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archivo, $m, (Split-Path -Leaf $m)) | Out-Null
        }
        # Comprobación: nada de secretos ni dependencias instaladas
        $prohibidas = $archivo.Entries | Where-Object {
            $_.FullName -match '(^|/)\.env$' -or $_.FullName -match '(^|/)(node_modules|venv|\.angular|__pycache__)/'
        }
        if ($prohibidas) { throw "El zip contiene ficheros que no deben entregarse: $($prohibidas.FullName -join ', ')" }
        $total = $archivo.Entries.Count
    } finally {
        $archivo.Dispose()
    }
    $mb = [math]::Round((Get-Item $zip).Length / 1MB, 1)
    "Zip creado: $zip ($total ficheros, $mb MB)"
} finally {
    Pop-Location
}

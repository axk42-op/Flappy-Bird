# Builds a self-contained Windows .exe and copies the Python backend into dist/
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$gameRoot = Split-Path -Parent $root
$dist = Join-Path $root "dist"
$proj = Join-Path $root "GalacticFrontier\GalacticFrontier.csproj"

Write-Host "Publishing Galactic Frontier..."
dotnet publish $proj -c Release -r win-x64 --self-contained true `
    -p:PublishSingleFile=true `
    -p:IncludeNativeLibrariesForSelfExtract=true `
    -o $dist

$backend = @(
    "bridge_server.py", "databaselogic.py", "database.py",
    "game_data.py", "users_store.py"
)
foreach ($f in $backend) {
    $src = Join-Path $gameRoot $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $dist $f) -Force
        Write-Host "Copied $f"
    }
}

Write-Host ""
Write-Host "Done. Run: $dist\Play Galactic Frontier.bat"
Write-Host "Requires: Python 3 + pip install bcrypt"

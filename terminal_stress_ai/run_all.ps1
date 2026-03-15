param(
  [string]$Session = "user1",
  [int]$Port = 8000,
  [string]$GrokApiKey = "",
  [string]$GrokModel = "grok-3-mini"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

if ($GrokApiKey -ne "") {
  $env:GROK_API_KEY = $GrokApiKey
}

if ($GrokModel -ne "") {
  $env:GROK_MODEL = $GrokModel
}

# Try to free port if already occupied.
try {
  $pids = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($pid in $pids) { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue }
} catch {
}

$server = Start-Process -FilePath py -ArgumentList "app\main.py", "--port", "$Port" -PassThru -WindowStyle Hidden

$ok = $false
for ($i = 0; $i -lt 25; $i++) {
  Start-Sleep -Milliseconds 300
  try {
    $health = py -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:$Port/health').read().decode())"
    $ok = $true
    break
  } catch {
  }
}

if (-not $ok) {
  Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
  throw "Server did not start on port $Port"
}

Write-Host "Server started on http://127.0.0.1:$Port (PID=$($server.Id))"
Write-Host "LLM mode: enabled (fallback if unavailable)"

try {
  py capture_terminal.py --session $Session --api "http://127.0.0.1:$Port"
} finally {
  Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
  Write-Host "Server stopped (PID=$($server.Id))"
}

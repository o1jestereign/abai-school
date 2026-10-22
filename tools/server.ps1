# =======================================================================
# Абай мектебі — Zero-Dependency Native Windows HTTP Server (PowerShell)
# =======================================================================
param([int]$Port = 8765)

# Ensure UTF-8 output encoding in console
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$root = Split-Path -Parent $PSScriptRoot
if (-not $root) { $root = (Get-Item -Path ".\").FullName }

$mimeTypes = @{
    ".html" = "text/html; charset=utf-8"
    ".htm"  = "text/html; charset=utf-8"
    ".css"  = "text/css; charset=utf-8"
    ".js"   = "application/javascript; charset=utf-8"
    ".json" = "application/json; charset=utf-8"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".jpeg" = "image/jpeg"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
    ".pdf"  = "application/pdf"
    ".txt"  = "text/plain; charset=utf-8"
}

# Try finding an open port starting from $Port
$listener = $null
$selectedPort = $Port
for ($p = $Port; $p -le $Port + 30; $p++) {
    try {
        $l = New-Object System.Net.HttpListener
        $l.Prefixes.Add("http://localhost:$p/")
        $l.Prefixes.Add("http://127.0.0.1:$p/")
        $l.Start()
        $listener = $l
        $selectedPort = $p
        break
    } catch {
        if ($l) {
            try { $l.Close() } catch {}
        }
    }
}

if (-not $listener) {
    Write-Host "[ҚАТЕ] Портты ашу мүмкін болмады (8765-8795 бос емес)." -ForegroundColor Red
    exit 1
}

$url = "http://localhost:$selectedPort/index.html"
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "      АБАЙ АТЫНДАҒЫ МЕКТЕП — 2D НАВИГАЦИЯ ЖҮЙЕСІ        " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  [+] Жүйе сәтті қосылды!" -ForegroundColor Green
Write-Host "  [+] Мекенжай: $url" -ForegroundColor White
Write-Host "  [+] Браузер автоматты түрде ашылуда..." -ForegroundColor Cyan
Write-Host "  [!] Тоқтату үшін осы терезені жабыңыз (немесе Ctrl+C)" -ForegroundColor Gray
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

Start-Process $url

try {
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $req = $ctx.Request
        $res = $ctx.Response

        try {
            $rawPath = $req.Url.LocalPath.TrimStart('/')
            if ([string]::IsNullOrWhiteSpace($rawPath)) { $rawPath = "index.html" }
            $decodedPath = [System.Uri]::UnescapeDataString($rawPath).Replace('/', [System.IO.Path]::DirectorySeparatorChar)
            $filePath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($root, $decodedPath))

            if (-not $filePath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase) -or -not [System.IO.File]::Exists($filePath)) {
                $res.StatusCode = 404
                $msg = [System.Text.Encoding]::UTF8.GetBytes("404 Not Found")
                $res.ContentType = "text/plain; charset=utf-8"
                $res.ContentLength64 = $msg.Length
                if ($req.HttpMethod -ne "HEAD") {
                    $res.OutputStream.Write($msg, 0, $msg.Length)
                }
            } else {
                $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                $mime = "application/octet-stream"
                if ($mimeTypes.ContainsKey($ext)) {
                    $mime = $mimeTypes[$ext]
                }
                $bytes = [System.IO.File]::ReadAllBytes($filePath)
                $res.StatusCode = 200
                $res.ContentType = $mime
                $res.ContentLength64 = $bytes.Length
                $res.Headers.Add("Cache-Control", "no-cache")
                if ($req.HttpMethod -ne "HEAD") {
                    $res.OutputStream.Write($bytes, 0, $bytes.Length)
                }
            }
        } catch {
            $res.StatusCode = 500
        } finally {
            try { $res.Close() } catch {}
        }
    }
} finally {
    if ($listener) {
        try {
            $listener.Stop()
            $listener.Close()
        } catch {}
    }
}

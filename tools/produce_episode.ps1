<#
.SYNOPSIS
  Guion YAML -> lint -> render (Docker) -> miniatura -> gate de packaging -> subida programada.

.DESCRIPTION
  Un solo comando por episodio. Se para en el primer paso que falla y no sube
  nada que no pase el lint de gancho/ritmo ni el gate de packaging: esos son
  los dos filtros que los cinco primeros videos no tenian.

  El video se sube PRIVADO con hora de publicacion (-PublishAt). YouTube lo
  hace publico solo a esa hora; hasta entonces se puede retirar con
  `facelessyt publish --video-id ... --privacy private`. Eso es lo que hace
  posible dejarlo desatendido sin renunciar a la ventana de revision.

.EXAMPLE
  .\tools\produce_episode.ps1 -Script scripts\06-queue.yaml `
      -ThumbFigure "2x" -ThumbHeadline "Same speed with 8 workers" -ThumbSub "the queue moved" `
      -ThumbText "2x same speed 8 workers" -PublishAt "2026-09-21T14:00" -Music D:\music\loop.mp3

.EXAMPLE
  # Imagen de ChatGPT/DALL-E SIN texto como fondo; el texto lo pone el codigo.
  .	ools\produce_episode.ps1 -Script scripts-queue.yaml -Background D:	humbs-bg.png `
      -ThumbFigure "2x" -ThumbHeadline "Same speed with 8 workers" `
      -ThumbText "2x same speed 8 workers" -PublishAt "2026-09-21T14:00"

.EXAMPLE
  # Con miniatura hecha fuera (image_gen, Canva...): se audita igual.
  .\tools\produce_episode.ps1 -Script scripts\06-queue.yaml -Thumbnail D:\thumbs\06.jpg `
      -ThumbText "2x same speed 8 workers" -PublishAt "2026-09-21T14:00"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $Script,
    [Parameter(Mandatory)] [string] $ThumbText,
    [string] $PublishAt,
    [switch] $Public,
    [string] $Thumbnail,
    [string] $Background,
    [string] $ThumbFigure,
    [string] $ThumbHeadline,
    [string] $ThumbSub = "",
    [string] $ThumbPanel = "amber",
    [string] $Music,
    [string] $Tags = "ai automation,python,indie software",
    [switch] $SkipRender,
    [switch] $DryRun
)

$ErrorActionPreference = "Stop"
if (-not $Public -and -not $PublishAt) { Write-Host "Hace falta -PublishAt (programado) o -Public (directo)." -ForegroundColor Red; exit 1 }
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"
Set-Location $Root

# Cama musical por defecto: la que genera tools/make_music_loop.py (sin licencias).
if (-not $Music -and (Test-Path (Join-Path $Root "data\music\loop.mp3"))) { $Music = Join-Path $Root "data\music\loop.mp3" }

function Step($name) { Write-Host "`n=== $name" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "`nPARADO: $msg" -ForegroundColor Red; exit 1 }

$spec = & $Py -c "import yaml,sys; v=yaml.safe_load(open(sys.argv[1],encoding='utf-8'))['video']; print(v['id']); print(v['title'])" $Script
$VideoId = $spec[0]; $Title = $spec[1]
$OutDir = Join-Path $Root "data\video\$VideoId"
$Mp4 = Join-Path $Root "data\video\$VideoId.mp4"
$Description = Join-Path $OutDir "description.txt"
New-Item -ItemType Directory -Force $OutDir | Out-Null

Step "1/5 Lint de gancho y ritmo"
& $Py -m facelessyt.video check --script $Script
if ($LASTEXITCODE -ne 0) { Fail "el guion no pasa el lint. Arregla los errores; no se renderiza." }

Step "2/5 Miniatura"
if (-not $Thumbnail) {
    if (-not $ThumbHeadline) { Fail "sin -Thumbnail hace falta -ThumbHeadline (y -ThumbFigure)." }
    $Thumbnail = Join-Path $OutDir "thumbnail.jpg"
    if ($Background) {
        & $Py -c "from pathlib import Path; from facelessyt.video import thumbnail as t; import sys; p=t.render_over_image(Path(sys.argv[1]), Path(sys.argv[2]), headline=sys.argv[3], figure=sys.argv[4], panel=sys.argv[5]); t.legibility_check(p); print(p)" $Background $Thumbnail $ThumbHeadline $ThumbFigure $ThumbPanel
    } else {
        if (-not $ThumbFigure) { Fail "sin -Background hace falta -ThumbFigure." }
        & $Py -c "from pathlib import Path; from facelessyt.video import thumbnail as t; import sys; p=t.render_bold(Path(sys.argv[1]), headline=sys.argv[2], figure=sys.argv[3], sub=sys.argv[4], panel=sys.argv[5]); t.legibility_check(p); print(p)" $Thumbnail $ThumbHeadline $ThumbFigure $ThumbSub $ThumbPanel
    }
    if ($LASTEXITCODE -ne 0) { Fail "no se pudo generar la miniatura." }
}

Step "3/5 Gate de packaging (titulo + texto + imagen)"
& $Py -m facelessyt packaging --title $Title --thumb-text $ThumbText --thumbnail $Thumbnail
if ($LASTEXITCODE -ne 0) { Fail "el packaging no pasa los umbrales. Con CTR del 1% no se sube mas de lo mismo." }

Step "4/5 Render en Docker (Piper + ffmpeg)"
if (-not $SkipRender) {
    # La imagen copia src/ dentro: si algo de src/ o el Dockerfile es mas nuevo
    # que la imagen, hay que reconstruirla o renderiza con codigo viejo.
    $created = docker image inspect facelessyt-video --format "{{.Created}}" 2>$null
    $newest = (Get-ChildItem (Join-Path $Root "src") -Recurse -File | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    $dockerfile = (Get-Item (Join-Path $Root "Dockerfile.video")).LastWriteTimeUtc
    if (-not $created -or [datetime]::Parse($created).ToUniversalTime() -lt $newest -or [datetime]::Parse($created).ToUniversalTime() -lt $dockerfile) {
        Write-Host "  imagen facelessyt-video desactualizada: reconstruyendo"
        docker build -q -f Dockerfile.video -t facelessyt-video .
        if ($LASTEXITCODE -ne 0) { Fail "no se pudo construir la imagen de video." }
    }
    $mounts = @("--mount", "type=bind,source=$Root,target=/work")
    # Si hay clave de ElevenLabs en el entorno (o en .env), el contenedor la usa
    # y `render --engine auto` elige esa voz en vez de Piper.
    foreach ($line in (Get-Content (Join-Path $Root ".env") -ErrorAction SilentlyContinue)) {
        if ($line -match '^\s*(ELEVENLABS_API_KEY|ELEVENLABS_VOICE_ID)\s*=\s*(.+)$') {
            Set-Item -Path "env:$($Matches[1])" -Value $Matches[2].Trim()
        }
    }
    if ($env:ELEVENLABS_API_KEY) { $mounts += @("-e", "ELEVENLABS_API_KEY", "-e", "ELEVENLABS_VOICE_ID") }
    $musicArg = @()
    if ($Music) {
        $mounts += @("--mount", "type=bind,source=$Music,target=/work/music.mp3,readonly")
        $musicArg = @("--music", "/work/music.mp3")
    }
    $rel = (Resolve-Path $Script).Path.Substring($Root.Length).TrimStart('\').Replace('\', '/')
    $env:MSYS_NO_PATHCONV = "1"
    docker run --rm @mounts -w /work facelessyt-video render `
        --script "/work/$rel" --workdir "/work/data/video/$VideoId" --out "/work/data/video/$VideoId.mp4" @musicArg
    if ($LASTEXITCODE -ne 0) { Fail "el render fallo." }
} else { Write-Host "  (saltado: -SkipRender)" }
if (-not (Test-Path $Mp4)) { Fail "no existe $Mp4" }

if (-not (Test-Path $Description)) {
    # Descripcion minima: el guion puede traer 'description' en video:; si no,
    # titulo + capitulos reales del montaje + repo.
    $desc = & $Py -c "import yaml,sys; print(yaml.safe_load(open(sys.argv[1],encoding='utf-8'))['video'].get('description',''))" $Script
    $chapters = Get-Content (Join-Path $OutDir "chapters.txt") -Raw
    @($desc, "", "Chapters:", $chapters, "", "Code (MIT): https://github.com/tapaderuza/facelessyt") -join "`n" |
        Out-File -Encoding utf8 $Description
}

if ($Public) { Step "5/5 Subida PUBLICA directa" } else { Step "5/5 Subida privada con publicacion programada ($PublishAt)" }
if ($DryRun) { Write-Host "  (dry run: no se sube)"; exit 0 }
if ($Public) { $visibility = @("--privacy", "public") } else { $visibility = @("--publish-at", $PublishAt) }
& $Py -m facelessyt upload --video $Mp4 --title $Title --description $Description `
    --thumbnail $Thumbnail --thumb-text $ThumbText --tags $Tags @visibility
if ($LASTEXITCODE -ne 0) { Fail "la subida fallo o el gate la paro." }
if ($Public) { Write-Host "`nPublicado." -ForegroundColor Green } else { Write-Host "`nListo. Revisalo en YouTube Studio antes de la hora programada." -ForegroundColor Green }

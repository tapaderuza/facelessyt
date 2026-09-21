<#
.SYNOPSIS
  Diagnostico semanal desatendido: CTR + retencion (`diagnose`) y metrica de corte (`track`).

.DESCRIPTION
  Guarda la salida en data/diagnose/<fecha>.txt y anade una linea a
  data/history.jsonl (lo hace `track`). Con eso, la decision del dia 90 sale
  de una serie y no de una foto.

  Registrar como tarea semanal (lunes 09:00), una sola vez, desde PowerShell:

    .\tools\weekly_diagnose.ps1 -Register

  Quitar: Unregister-ScheduledTask -TaskName FacelessYT-WeeklyDiagnose -Confirm:$false
#>
[CmdletBinding()]
param([switch] $Register)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"

if ($Register) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" `
        -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -WorkingDirectory $Root
    # Dos disparadores: lunes 09:00, y ademas cada inicio de sesion. El
    # 2026-09-21 el PC estaba apagado a las 09:00 y Windows salto la ejecucion
    # a la semana siguiente. Con el disparador de inicio de sesion se recupera;
    # el propio script evita repetir si esta semana ya se ejecuto.
    $triggers = @(
        (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 09:00),
        (New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME")
    )
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName "FacelessYT-WeeklyDiagnose" -Action $action -Trigger $triggers `
        -Settings $settings -Description "CTR, retencion y metrica de corte del canal" -Force | Out-Null
    Write-Host "Tarea registrada: FacelessYT-WeeklyDiagnose (lunes 09:00 + al iniciar sesion, una vez por semana)."
    exit 0
}

Set-Location $Root
$outDir = Join-Path $Root "data\diagnose"
New-Item -ItemType Directory -Force $outDir | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd"
$log = Join-Path $outDir "$stamp.txt"

# Una ejecucion por semana ISO: el disparador de inicio de sesion salta cada
# dia, pero solo trabaja si esta semana no hay informe todavia.
$monday = (Get-Date).Date.AddDays(-(([int](Get-Date).DayOfWeek + 6) % 7))
$week = "week-of-" + $monday.ToString("yyyy-MM-dd")
$marker = Join-Path $outDir "$week.done"
if (Test-Path $marker) { exit 0 }

"== diagnose (28 dias) $stamp" | Out-File -Encoding utf8 $log
& $Py -m facelessyt diagnose --days 28 2>&1 | Out-File -Encoding utf8 -Append $log
"`n== track" | Out-File -Encoding utf8 -Append $log
& $Py -m facelessyt track 2>&1 | Out-File -Encoding utf8 -Append $log
Get-Content $log
$stamp | Out-File -Encoding utf8 $marker

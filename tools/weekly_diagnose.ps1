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
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 09:00
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
    Register-ScheduledTask -TaskName "FacelessYT-WeeklyDiagnose" -Action $action -Trigger $trigger `
        -Settings $settings -Description "CTR, retencion y metrica de corte del canal" -Force | Out-Null
    Write-Host "Tarea registrada: FacelessYT-WeeklyDiagnose (lunes 09:00)."
    exit 0
}

Set-Location $Root
$outDir = Join-Path $Root "data\diagnose"
New-Item -ItemType Directory -Force $outDir | Out-Null
$stamp = Get-Date -Format "yyyy-MM-dd"
$log = Join-Path $outDir "$stamp.txt"

"== diagnose (28 dias) $stamp" | Out-File -Encoding utf8 $log
& $Py -m facelessyt diagnose --days 28 2>&1 | Out-File -Encoding utf8 -Append $log
"`n== track" | Out-File -Encoding utf8 -Append $log
& $Py -m facelessyt track 2>&1 | Out-File -Encoding utf8 -Append $log
Get-Content $log

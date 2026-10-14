# 3 akkauntni har birini alohida oynada ishga tushiradi.
# Ishlatish:  .\run_all.ps1
# (avval har akkauntga bir marta login qilingan bo'lishi kerak)

$root = $PSScriptRoot
$py = Join-Path $root "venv\Scripts\python.exe"

foreach ($acc in @("acc1", "acc2", "acc3")) {
    Write-Host "Ishga tushmoqda: $acc" -ForegroundColor Green
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "Set-Location '$root'; & '$py' userbot.py $acc"
    )
    Start-Sleep -Seconds 2
}

Write-Host "3 akkaunt alohida oynalarda ishga tushdi." -ForegroundColor Cyan

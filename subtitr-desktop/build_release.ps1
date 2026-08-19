# $ErrorActionPreference'ni "Stop" qilmaymiz: PyInstaller/Flutter progress'ni
# stderr'ga yozadi va bu native chiqishni PowerShell xato deb hisoblab qoladi.
# Buning o'rniga har bir muhim qadamdan keyin exit kodini tekshiramiz.
$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot
Set-Location $Root

function Assert-LastExit([string]$step) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "XATO: '$step' qadami $LASTEXITCODE kod bilan tugadi." -ForegroundColor Red
        exit 1
    }
}

# Ixtiyoriy kod-imzolash (SmartScreen ogohlantirishini kamaytiradi).
# Sertifikat berilsa imzolaydi:
#   $env:SUBTITR_SIGN_PFX  = "C:\yo'l\cert.pfx";  $env:SUBTITR_SIGN_PASS = "parol"
#   yoki  $env:SUBTITR_SIGN_THUMB = "<sertifikat thumbprint>"  (Windows cert do'konidan)
function Sign-Files([string[]]$paths) {
    $cert = $null
    try {
        if ($env:SUBTITR_SIGN_PFX -and (Test-Path $env:SUBTITR_SIGN_PFX)) {
            $pw = ConvertTo-SecureString $env:SUBTITR_SIGN_PASS -AsPlainText -Force
            $cert = Get-PfxCertificate -FilePath $env:SUBTITR_SIGN_PFX -Password $pw -ErrorAction Stop
        } elseif ($env:SUBTITR_SIGN_THUMB) {
            $cert = Get-ChildItem "Cert:\CurrentUser\My\$($env:SUBTITR_SIGN_THUMB)" -ErrorAction Stop
        }
    } catch { $cert = $null }
    if (-not $cert) { return $false }
    foreach ($p in $paths) {
        if (Test-Path $p) {
            try {
                Set-AuthenticodeSignature -FilePath $p -Certificate $cert `
                    -TimestampServer "http://timestamp.digicert.com" -ErrorAction Stop | Out-Null
                Write-Host "    imzolandi: $(Split-Path $p -Leaf)" -ForegroundColor DarkGray
            } catch { Write-Host "    imzo xato: $(Split-Path $p -Leaf)" -ForegroundColor Yellow }
        }
    }
    return $true
}

Write-Host "1/6  PyInstaller tekshirilyapti..." -ForegroundColor Cyan
python -m pip install --quiet --upgrade pyinstaller
Assert-LastExit "pip install pyinstaller"

Write-Host "2/6  Python protsessorni yig'ish (desktop_processor.exe)..." -ForegroundColor Cyan
python -m PyInstaller --clean --noconfirm desktop_processor.spec
Assert-LastExit "PyInstaller"

Write-Host "3/6  Flutter Windows release build..." -ForegroundColor Cyan
Push-Location subtitr_app
flutter build windows --release
$flutterExit = $LASTEXITCODE
Pop-Location
if ($flutterExit -ne 0) {
    Write-Host "XATO: Flutter build $flutterExit kod bilan tugadi." -ForegroundColor Red
    exit 1
}

Write-Host "4/6  Tayyor paket (Subtitr-Release) yig'ilyapti..." -ForegroundColor Cyan
$ReleaseDir = Join-Path $Root "Subtitr-Release"
if (Test-Path $ReleaseDir) { Remove-Item -Recurse -Force $ReleaseDir }
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

# Flutter build natijasi (exe + DLL + data)
Copy-Item -Path "subtitr_app\build\windows\x64\runner\Release\*" -Destination $ReleaseDir -Recurse -Force

# Python protsessor
Copy-Item -Path "dist\desktop_processor.exe" -Destination $ReleaseDir -Force

# ffmpeg / ffprobe / yt-dlp — tools papkasidan (to'liq binarlar; PATH shim'lariga ishonmaymiz)
$Tools = Join-Path $Root "tools"
foreach ($t in @("ffmpeg.exe", "ffprobe.exe", "yt-dlp.exe")) {
    $src = Join-Path $Tools $t
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $ReleaseDir -Force
    } else {
        Write-Host "  DIQQAT: $t topilmadi ($src). tools papkasiga to'liq binarni qo'ying." -ForegroundColor Yellow
    }
}

# .env NAMUNASI — hech qachon haqiqiy .env (kalitlar bilan) emas!
Copy-Item -Path ".env.example" -Destination "$ReleaseDir\.env.example" -Force

# Ixtiyoriy: paketdagi exe'larни imzolash (installerdan oldin).
$signed = Sign-Files @("$ReleaseDir\subtitr_app.exe", "$ReleaseDir\desktop_processor.exe")

Write-Host "5/6  O'rnatuvchi (SubtitrSetup.exe) yasalyapti..." -ForegroundColor Cyan
$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($iscc) {
    & $iscc "installer.iss"
    Assert-LastExit "Inno Setup (ISCC)"
    Sign-Files @("$Root\installer\SubtitrSetup.exe") | Out-Null
    Write-Host "    -> installer\SubtitrSetup.exe tayyor" -ForegroundColor Green
} else {
    Write-Host "  DIQQAT: Inno Setup (ISCC.exe) topilmadi." -ForegroundColor Yellow
    Write-Host "  O'rnating:  winget install JRSoftware.InnoSetup" -ForegroundColor Yellow
}

Write-Host "6/6  Portable ZIP arxiv..." -ForegroundColor Cyan
$Zip = Join-Path $Root "Subtitr-Release.zip"
if (Test-Path $Zip) { Remove-Item -Force $Zip }
Compress-Archive -Path "$ReleaseDir\*" -DestinationPath $Zip

Write-Host ""
Write-Host "TAYYOR!" -ForegroundColor Green
Write-Host "  * O'rnatuvchi:  installer\SubtitrSetup.exe   (Telegram/internetga tashlash uchun)" -ForegroundColor Green
Write-Host "  * Portable ZIP: Subtitr-Release.zip" -ForegroundColor Green
if (-not $signed) {
    Write-Host ""
    Write-Host "  ESLATMA: fayllar imzolanmadi -> yuklaganda Windows SmartScreen" -ForegroundColor Yellow
    Write-Host "  'Noma'lum nashriyot' ogohlantirishi chiqaradi. Bu normal." -ForegroundColor Yellow
    Write-Host "  Foydalanuvchi: 'Batafsil' -> 'Baribir ishga tushirish' bosadi." -ForegroundColor Yellow
    Write-Host "  Ogohlantirishni butunlay olib tashlash uchun kod-imzolash" -ForegroundColor Yellow
    Write-Host "  sertifikati kerak (SUBTITR_SIGN_PFX/PASS yoki SUBTITR_SIGN_THUMB)." -ForegroundColor Yellow
}

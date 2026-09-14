#Requires -Version 5.1
<#
.SYNOPSIS
    SCARPION MUSIC — Windows uchun ishga tushirish skripti.

.DESCRIPTION
    Loyihani noldan ishga tayyorlaydi:
      1. Python 3.12+ ni topadi
      2. venv yaratadi va kutubxonalarni o'rnatadi
      3. .env faylini .env.example dan yasab, SECRET_KEY generatsiya qiladi
      4. Bazani yaratadi (migrate)
      5. Serverni ishga tushiradi va brauzerni ochadi

    Takroriy ishga tushirishda tayyor qismlarni o'tkazib yuboradi.

.PARAMETER Port
    Server porti. Sukut bo'yicha 8000.

.PARAMETER Tarmoq
    Serverni butun Wi-Fi tarmog'iga ochadi — telefondan ham kirish mumkin.

.PARAMETER Albom
    Bazaga mashhur albomlarni yuklaydi (internet talab qiladi, ~5 daqiqa).

.PARAMETER Admin
    Admin panel uchun foydalanuvchi yaratishni so'raydi.

.EXAMPLE
    .\ishga-tushir.ps1
    Oddiy ishga tushirish.

.EXAMPLE
    .\ishga-tushir.ps1 -Albom -Admin
    Birinchi marta: albomlarni yuklab, admin ham yaratadi.

.EXAMPLE
    .\ishga-tushir.ps1 -Tarmoq
    Telefondan ham ochish uchun.
#>

[CmdletBinding()]
param(
    [int]$Port = 8000,
    [switch]$Tarmoq,
    [switch]$Albom,
    [switch]$Admin
)

$ErrorActionPreference = 'Stop'

# Konsol o'zbekcha harflarni to'g'ri ko'rsatsin
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# Skript qaysi papkada bo'lsa, o'sha yerda ishlaymiz.
# Busiz VS Code boshqa papkadan chaqirsa fayllar topilmasdi.
Set-Location -Path $PSScriptRoot

function Bosqich  { param([string]$M) Write-Host ""; Write-Host ">> $M" -ForegroundColor Cyan }
function Yaxshi   { param([string]$M) Write-Host "   [OK] $M" -ForegroundColor Green }
function Ogoh     { param([string]$M) Write-Host "   [!]  $M" -ForegroundColor Yellow }
function Xatolik  { param([string]$M) Write-Host "   [X]  $M" -ForegroundColor Red }
function Satr     { param([string]$M) Write-Host "        $M" -ForegroundColor DarkGray }

function Save-EnvFile {
    <#
      .env ni BOM SIZ saqlaydi.

      PowerShell 5.1 da "Set-Content -Encoding UTF8" faylni BOM bilan
      yozadi. python-dotenv BOM ni o'zi tashlab yuboradi, lekin boshqa
      vositalar (tahrirlagich, git diff) uni begona belgi deb ko'rsatishi
      mumkin. .NET orqali yozganda BOM umuman tushmaydi.
    #>
    param([Parameter(Mandatory=$true)][string]$Matn)
    $kodlash = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot '.env'), $Matn, $kodlash)
}

Write-Host ""
Write-Host "  SCARPION MUSIC" -ForegroundColor Magenta
Write-Host "  ==============" -ForegroundColor Magenta

# ------------------------------------------------------------------
# 1. Python
# ------------------------------------------------------------------
Bosqich "Python qidirilmoqda (3.12 yoki undan yangi kerak)"

function Find-Python {
    # Windows da uch xil chaqiruv bo'lishi mumkin. Har birini sinaymiz
    # va versiyasini so'raymiz — Django 6.1 uchun 3.12+ shart.
    $variantlar = @(
        @{ Fayl = 'py';      Arg = @('-3') },
        @{ Fayl = 'python';  Arg = @() },
        @{ Fayl = 'python3'; Arg = @() }
    )
    foreach ($v in $variantlar) {
        if (-not (Get-Command $v.Fayl -ErrorAction SilentlyContinue)) { continue }
        $kod = 'import sys; print("%d.%d" % sys.version_info[:2])'
        try   { $chiqish = & $v.Fayl @($v.Arg + @('-c', $kod)) 2>$null }
        catch { continue }
        if (-not $chiqish) { continue }

        $qismlar = ("$chiqish").Trim().Split('.')
        if ($qismlar.Count -lt 2) { continue }
        $katta = [int]$qismlar[0]
        $kichik = [int]$qismlar[1]
        if ($katta -eq 3 -and $kichik -ge 12) {
            return @{ Fayl = $v.Fayl; Arg = $v.Arg; Versiya = "$katta.$kichik" }
        }
        Satr "$($v.Fayl) topildi, lekin versiyasi $katta.$kichik — yaramaydi"
    }
    return $null
}

$py = Find-Python
if ($null -eq $py) {
    Xatolik "Python 3.12 yoki undan yangisi topilmadi."
    Satr "Yuklab oling: https://www.python.org/downloads/"
    Satr "O'rnatishda 'Add Python to PATH' katagini BELGILANG."
    exit 1
}
Yaxshi "Python $($py.Versiya) topildi"

# ------------------------------------------------------------------
# 2. Virtual muhit
# ------------------------------------------------------------------
$VenvPython = Join-Path $PSScriptRoot 'venv\Scripts\python.exe'

if (Test-Path $VenvPython) {
    Yaxshi "venv allaqachon bor"
} else {
    Bosqich "venv yaratilmoqda"
    & $py.Fayl @($py.Arg + @('-m', 'venv', 'venv'))
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPython)) {
        Xatolik "venv yaratilmadi."
        exit 1
    }
    Yaxshi "venv yaratildi"
}

# ------------------------------------------------------------------
# 3. Kutubxonalar
# ------------------------------------------------------------------
Bosqich "Kutubxonalar tekshirilmoqda"

# Django bormi? Bo'lsa qaytadan o'rnatmaymiz — bu har safar
# bir necha daqiqa vaqtni tejaydi.
# try/catch SHART: $ErrorActionPreference = 'Stop' turganda tashqi
# buyruqning stderr i yo'naltirilsa (2>$null), PowerShell uni to'xtovchi
# xatoga aylantirib yuborishi mumkin. Bizga esa faqat natija kerak.
$djangoBor = $false
try {
    & $VenvPython -c "import django" 2>$null
    $djangoBor = ($LASTEXITCODE -eq 0)
} catch {
    $djangoBor = $false
}

if ($djangoBor) {
    Yaxshi "Kutubxonalar o'rnatilgan"
} else {
    Satr "Bu bir necha daqiqa olishi mumkin..."
    & $VenvPython -m pip install --upgrade pip --quiet --disable-pip-version-check
    & $VenvPython -m pip install -r requirements.txt --quiet --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Xatolik "Kutubxonalarni o'rnatib bo'lmadi. Internetni tekshiring."
        exit 1
    }
    Yaxshi "Kutubxonalar o'rnatildi"
}

# ------------------------------------------------------------------
# 4. .env
# ------------------------------------------------------------------
if (Test-Path '.env') {
    Yaxshi ".env fayli bor"
} else {
    Bosqich ".env yaratilmoqda"
    if (-not (Test-Path '.env.example')) {
        Xatolik ".env.example topilmadi — loyiha to'liq ko'chirilmagan."
        exit 1
    }
    Copy-Item '.env.example' '.env'

    # Har bir o'rnatishda O'ZIGA XOS maxfiy kalit yaratamiz.
    # Bir xil kalitni baham ko'rish xavfli.
    $kod = 'from django.core.management.utils import get_random_secret_key as g; print(g())'
    $kalit = (& $VenvPython -c $kod).Trim()

    # DIQQAT: Django kaliti $ belgisini o'z ichiga oladi (masalan $8q4).
    # PowerShell ning -replace operatori almashtiruv matnidagi $8 ni
    # "8-guruhni qo'y" deb tushunadi va uni o'chirib yuboradi — kalit
    # buzilgan holda yoziladi. $$ esa bitta haqiqiy $ degani.
    # .Replace() oddiy matn almashtirish, regex emas — shuning uchun
    # aynan shu bilan ekranlaymiz.
    $kalitXavfsiz = $kalit.Replace('$', '$$')

    $matn = Get-Content '.env' -Raw
    $matn = $matn -replace '(?m)^SECRET_KEY=.*$', "SECRET_KEY=$kalitXavfsiz"
    $matn = $matn -replace '(?m)^MUSIC_PROVIDER=.*$', 'MUSIC_PROVIDER=deezer'
    Save-EnvFile -Matn $matn

    Yaxshi ".env yaratildi, SECRET_KEY generatsiya qilindi"
    Ogoh "Google bilan kirish uchun .env ga Firebase kalitlari kerak."
    Satr "Ularsiz ham sayt to'liq ishlaydi — oddiy parol bilan kiriladi."
}

# ------------------------------------------------------------------
# 5. Tarmoq rejimi
# ------------------------------------------------------------------
$Manzil = "127.0.0.1"
if ($Tarmoq) {
    Bosqich "Tarmoq rejimi"
    $ip = $null
    try {
        $ip = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
               Where-Object { $_.IPAddress -notlike '127.*' -and
                              $_.IPAddress -notlike '169.254.*' } |
               Select-Object -First 1).IPAddress
    } catch { }

    if ($ip) {
        # Django begona manzildan kelgan so'rovni ALLOWED_HOSTS da
        # bo'lmasa rad etadi — shuning uchun IP ni qo'shib qo'yamiz.
        $matn = Get-Content '.env' -Raw
        $matn = $matn -replace '(?m)^ALLOWED_HOSTS=.*$', "ALLOWED_HOSTS=127.0.0.1,localhost,$ip"
        Save-EnvFile -Matn $matn

        $Manzil = "0.0.0.0"
        Yaxshi "Telefondan oching: http://${ip}:$Port/"
        Ogoh "Ochilmasa Windows Defender faervoli so'raganda 'Allow' bosing."
    } else {
        Ogoh "Tarmoq IP manzili topilmadi — oddiy rejimda davom etamiz."
    }
}

# ------------------------------------------------------------------
# 6. Baza
# ------------------------------------------------------------------
Bosqich "Baza tayyorlanmoqda"
& $VenvPython manage.py migrate --noinput
if ($LASTEXITCODE -ne 0) { Xatolik "Migratsiya xato berdi."; exit 1 }
Yaxshi "Baza tayyor"

# ------------------------------------------------------------------
# 7. Albomlar
# ------------------------------------------------------------------
# Bazada nechta albom borligini bilib olamiz.
# "manage.py shell -c" birinchi qatorda ortiqcha xabar chiqaradi,
# shuning uchun OXIRGI qatorni olamiz va raqamligini tekshiramiz.
$albomSoni = 0
try {
    $kod = 'from music.models import Album; print(Album.objects.count())'
    $chiqish = & $VenvPython manage.py shell -c $kod 2>$null
    $oxirgi = "$($chiqish | Select-Object -Last 1)".Trim()
    if ($oxirgi -match '^\d+$') { $albomSoni = [int]$oxirgi }
} catch { $albomSoni = 0 }

if ($Albom -or $albomSoni -eq 0) {
    if ($albomSoni -eq 0 -and -not $Albom) {
        Bosqich "Baza bo'sh"
        # "y" ni qabul qilmaymiz: o'zbekchada u "yo'q" degani bo'lib,
        # foydalanuvchi rad etmoqchi bo'lganda ha deb tushunilardi.
        $javob = Read-Host "   Mashhur albomlarni yuklaymizmi? (~5 daqiqa) [ha / yo'q]"
        if ($javob -notmatch '^(h|ha)$') {
            Ogoh "O'tkazib yuborildi. Keyin: .\ishga-tushir.ps1 -Albom"
            $Albom = $false
        } else { $Albom = $true }
    }
    if ($Albom) {
        Bosqich "Albomlar yuklanmoqda (internet kerak)"
        & $VenvPython manage.py seed_albums
        Yaxshi "Albomlar yuklandi"
    }
} else {
    Yaxshi "Bazada $albomSoni ta albom bor"
}

# ------------------------------------------------------------------
# 8. Admin
# ------------------------------------------------------------------
if ($Admin) {
    Bosqich "Admin foydalanuvchi yaratilmoqda"
    Satr "Parol yozilayotganda ekranda ko'rinmaydi — bu normal."
    & $VenvPython manage.py createsuperuser
}

# ------------------------------------------------------------------
# 9. Ishga tushirish
# ------------------------------------------------------------------
Bosqich "Server ishga tushmoqda"
Write-Host ""
Write-Host "   Sayt:  http://127.0.0.1:$Port/" -ForegroundColor Green
Write-Host "   Admin: http://127.0.0.1:$Port/admin/" -ForegroundColor DarkGray
Write-Host ""
Write-Host "   To'xtatish uchun: Ctrl + C" -ForegroundColor DarkGray
Write-Host ""

# Brauzerni 3 soniyadan keyin ochamiz — server ko'tarilishi uchun vaqt.
# Start-Job alohida oqimda ishlaydi, serverni kutib turmaydi.
$null = Start-Job -ScriptBlock {
    param($p)
    Start-Sleep -Seconds 3
    Start-Process "http://127.0.0.1:$p/"
} -ArgumentList $Port

& $VenvPython manage.py runserver "${Manzil}:$Port"

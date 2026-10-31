# Subtitr Desktop — macOS

> macOS release'i GitHub Actions'ning `macos-latest` muhitida native tarzda
> yig'iladi va `.dmg` artifact sifatida tekshiriladi. Haqiqiy Mac qurilmasida
> foydalanuvchi oqimi sinovi hali alohida kerak; muammo bo'lsa
> [issue oching](https://github.com/shamsiyevshamsiddin19/vibe-coding/issues).
>
> Linux va Windows variantlari sinalgan va ishlaydi.

## 1. Kerakli dasturlar

```bash
brew install ffmpeg python@3.12
```

Qo'shimcha:

- **Xcode** (App Store'dan) va buyruq qatori vositalari:
  `xcode-select --install`
- **Flutter SDK** (3.27+) — [flutter.dev/docs/get-started/install/macos](https://docs.flutter.dev/get-started/install/macos)
- **CocoaPods**: `sudo gem install cocoapods`

Tekshirish: `flutter doctor` da "Xcode" yashil bo'lsin.

## 2. Yig'ish

```bash
git clone https://github.com/shamsiyevshamsiddin19/vibe-coding.git
cd vibe-coding/subtitr-desktop
./macos/build.sh
```

Natija:

- `dist/SubtitrDesktop-<versiya>-macos-<arch>.dmg` — o'rnatuvchi disk obrazi
- shu nomdagi `.dmg.sha256` — yuklamaning nazorat summasi

Apple Silicon (`arm64`) va Intel (`x86_64`) uchun alohida yig'iladi —
skript o'zi aniqlaydi.

Release ichidagi Python protsessor PyInstaller bilan binarga qotirilgan:
tayyor DMG'ni ishlatadigan foydalanuvchiga Python yoki Flutter o'rnatish
kerak emas. Lokal, model asosidagi transkripsiya manbadan yig'iladigan
variantda mavjud; release binari cloud API kalitlari bilan ishlaydi.

## 3. O'rnatish

```bash
ochilgan DMG ichidagi `install.sh` faylini ishga tushiring
```

Dastur `~/Applications/SubtitrDesktop` ga tushadi. Ishga tushirish:

```bash
open ~/Applications/SubtitrDesktop/*.app
```

O'chirish: `rm -rf ~/Applications/SubtitrDesktop`

## 4. Gatekeeper

Ilova Apple sertifikati bilan imzolanmagan va notarizatsiya qilinmagan,
shuning uchun macOS uni ochishdan bosh tortishi mumkin
(*"damaged and can't be opened"* yoki *"unidentified developer"*).

`install.sh` karantin belgisini o'zi olib tashlaydi. Qo'lda:

```bash
xattr -dr com.apple.quarantine ~/Applications/SubtitrDesktop
```

Yoki `.app` ustida **o'ng tugma → Open → Open**.

## 5. App Sandbox nega o'chirilgan

`subtitr_app/macos/Runner/Release.entitlements` da sandbox **o'chirilgan**.
Sababi: ilova yonidagi Python protsessorni ishga tushiradi, `ffmpeg` ni
chaqiradi va `~/Movies` / `~/Videos` papkasi bilan ishlaydi — sandbox ichida
bularning **hech biri** mumkin emas.

Demak bu build Mac App Store uchun yaramaydi. To'g'ridan-to'g'ri tarqatish
(yoki o'zingiz uchun yig'ish) uchun mo'ljallangan.

## 6. Birinchi ishga tushirish

Ilova ichida kalit tugmasini bosib **Groq** kalitini kiriting
([console.groq.com](https://console.groq.com) — bepul).

Natijalar `~/Videos/Subtitr natijalar` papkasiga tushadi (macOS'da bu odatda
`~/Movies` — yo'lni `SUBTITR_OUT_DIR` bilan o'zgartirish mumkin).

## 7. Kutilayotgan muammolar

Sinalmagani uchun quyidagilar ehtimoli bor:

- **`~/Videos` yo'q** — macOS'da standart papka `~/Movies`. Ilova ishga
  tushganda `~/Videos` ni yasaydi; boshqa joy kerak bo'lsa:
  `SUBTITR_KINO_DIR=~/Movies SUBTITR_OUT_DIR=~/Movies/Subtitr open ...`
- **Apparat kodlash** — macOS'da VideoToolbox bor, lekin kod uni hali
  tanimaydi; render CPU (`libx264`) bilan ketadi, ya'ni sekinroq.
- **CocoaPods xatolari** — `cd subtitr_app/macos && pod install --repo-update`

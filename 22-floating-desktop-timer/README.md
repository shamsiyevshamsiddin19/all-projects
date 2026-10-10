# ⏱ Suzuvchi Taymer (Floating Desktop Timer)

Linux (Ubuntu / GNOME) uchun maxsus ishlab chiqilgan, barcha ochiq dasturlar va oynalar ustida suzib turuvchi zamonaviy va ixcham desktop taymer vidjeti.

---

## ✨ Asosiy Imkoniyatlari

- 📌 **Always-on-Top (Har doim yuqorida):** Boshqa dasturlarga (VS Code, Chrome, Telegram va boshqalar) o'tsangiz ham, taymer doimo ko'rinib turadi.
- 🔄 **Barcha ish stollarida (Sticky Workspace):** Ish stollarini (Workspaces) almashtirsangiz ham o'z joyida qoladi.
- 🤏 **Mini-Pill Rejimi (O'ta ixcham):** Birgina tugma (`⊡`) bilan vidjetni ekranning chetiga xalal bermaydigan kichik kapsulaga aylantirish mumkin (`⏱ 24:50 | ⏸ | ⛶`).
- 🖐 **Erkin surish (Draggable):** Sichqoncha bilan ushlab, ekranning istalgan burchagiga qulay joylashtirish mumkin.
- ⚡ **Tezkor Presetlar:** 
  - `5d` — Qisqa tanaffus
  - `15d` — O'rtacha tanaffus
  - `25d` — Pomodoro fokus vaqti
  - `45d` — Dars yoki ish seansi
  - `60d` — 1 soatlik taymer
- ⏳ **Sekundomer rejimi:** Vaqtni to'g'ridan-to'g'ri sanash (Stopwatch).
- ➕/➖ **Tezkor sozlash:** `+1m`, `-1m`, `+5m`, `-5m` tugmalari orqali vaqtni darhol o'zgartirish.
- 🔔 **Ovoz va Bildirishnoma:** Belgilangan vaqt tugaganda tizim bildirishnomasi (`notify-send`) va jarangdor signal (`alarm-clock-elapsed`) chalinadi.
- ⌨️ **Klaviatura tezkor tugmalari:**
  - `Bo'shliq (Space)`: Boshlash / To'xtatish (Play / Pause)
  - `Esc`: Mini rejimga o'tish / qaytish

---

## 🚀 Ishga tushirish va O'rnatish

### 1. Tizimga o'rnatish (Ubuntu menyusiga qo'shish)
```bash
cd /home/shamsiddin/Documents/project/loyihalar/22-floating-desktop-timer
./install.sh
```

O'rnatilgach:
- Ubuntu ilovalar menyusidan **"Suzuvchi Taymer"** deb qidirib bir marta bosish orqali ochishingiz mumkin.
- Yoki terminalda istalgan joydan `floating-timer` buyrug'i orqali ochishingiz mumkin.

### 2. To'g'ridan-to'g'ri ishga tushirish
```bash
./run.sh
```
yoki
```bash
python3 main.py
```

---

## ⚙️ Texnologiyalar
- **Til:** Python 3
- **GUI & Grafika:** GTK+ 3, Cairo, GObject Introspection (Ubuntu uchun nativ)
- **Dizayn:** Glassmorphism Dark UI, zamonaviy CSS

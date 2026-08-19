# Slayd dizayn dvigatelini kuchaytirish — ish prompti

## Missiya
Slaydlar "yaxshi"dan "hayratlanarli professional"ga chiqsin: har slaydda
turlicha gradient/fon, boy va xilma-xil layout arxitekturalari. Ikkita talaba
bir mavzuda buyurtsa ham, slaydlar bir-biriga o'xshamasin, lekin har biri
puxta va uyg'un bo'lsin. Zaif server (498MB) — faqat sof-Python/XML, og'ir
kutubxona yo'q (python-pptx shakllari XML orqali chiziladi, arzon).

## 1. Gradient dvigateli (`_grad_xml` + `_apply_grad`)
OOXML gradFill XML'ni to'g'ridan-to'g'ri quraman (python-pptx 2-stopdan
nariga chiqmaydi). Uslublar:
- `diagonal` — 2-3 stop, burchak 35-55° (slaydga qarab aylanadi)
- `vertical` — tik gradient
- `tri` — 3 rangli (bg → oraliq → bg2), chuqurroq
- `radial` — markaziy yoki burchakdan tarqaladigan doiraviy nur
Har slayd indeksi bo'yicha uslub + burchak DETERMINIK aylanadi (variety,
lekin tasodifiy tartibsizlik emas).

## 2. Bezak dvigateli (`_decorate`)
Fon ustiga, matn ostiga — nozik (alpha 8-22%) bezaklar. Uslublar:
- `blobs` — 2-3 katta shaffof doira (burchaklarda)
- `band` — diagonal/tik shaffof lenta
- `sidebar` — chapda rangli panel (sidebar layout uchun)
- `wedge` — burchak uchburchagi
- `dots` — burchakda mayda nuqtalar to'ri
- `rings` — konsentrik doira konturlari
Har slaydda 1-2 bezak, mavzu rangida.

## 3. Ranglar palitrasi — 6 ta mavzu
Har biri: bg, bg2, bg3 (tri uchun), accent, accent2, title, text, card.
Mavzu hashidan tanlanadi (barqarorlik) + ichida gradient/bezak aylanadi.

## 4. Yangi layout arxitekturalari
Mavjud (cover/content/two_col/stat/quote/chart/image/end) + yangi:
- `section` — bo'lim ajratuvchi: katta raqam + bo'lim nomi, minimal, rangli panel
- `steps` — 3-4 raqamlangan bosqich, gorizontal oqim (jarayon/algoritm uchun)
- `cards` — 2×2 yoki 3-li kartochka to'ri (points → ikonli kartochkalar)
- `timeline` — gorizontal vaqt o'qi, nuqtalar bilan (tarix/bosqichlar uchun)
Mavjudlarni ham yaxshilash: assimetrik kompozitsiya, aksent shakllar,
yaxshiroq tipografiya va oraliq.

## 5. Prompt yangilash (`ai/prompts.py slayd()`)
AI'ga yangi layoutlarni o'rgatish (section/steps/cards/timeline), qachon
qo'llashni tushuntirish. Har taqdimotda xilma-xillik talab qilish (bir xil
layout ketma-ket kelmasin; kamida 4-5 xil layout ishlatilsin).

## 6. Test + deploy
Lokal: barcha layout+gradient+bezak kombinatsiyasini render qilib, fayl
python-pptx bilan qayta o'qilishini (yaroqli XML) tekshirish. Server: deploy,
real mavzu bilan jonli sinov, faylni foydalanuvchiga ko'rsatish.

## Xavfsizlik qoidalari
- Har bezak/gradient try/except bilan — xato bo'lsa oddiy fonga tushsin,
  taqdimot hech qachon buzilmasin.
- Bezaklar nozik: matn o'qilishiga xalaqit bermasin (past alpha, chekkalarda).
- Pexels fon-foto ustiga bezak QO'YILMAYDI (foto o'zi boy).

# 04 — Xavfsizlik va suiiste'mol (eng muhim hujjat)

> Biz **begona, tekshirilmagan kod**ni o'z serverimizda ishga tushiramiz.
> Buning ustiga o'sha kodni **AI yozgan** — ya'ni muallif uning nima
> qilayotganini to'liq bilmasligi mumkin. Bu oddiy sayt hostingidan
> tubdan boshqa xatar darajasi.
>
> Hosting loyihalarining aksariyati texnik sababdan emas, **suiiste'mol**
> sababdan yopiladi: IP qora ro'yxatga tushadi, provayder akkauntni
> bloklaydi, yoki huquqiy muammo chiqadi.

## 4.1 Xatarlar va qarshi choralar

### Konteynerdan chiqish (container escape)
| Chora | Bosqich |
|---|---|
| `--cap-drop=ALL`, kerakli minimumni qaytarish | 1 |
| `--security-opt no-new-privileges` | 1 |
| Docker `userns-remap` — konteyner root ≠ host root | 1 |
| `--read-only` rootfs + `/tmp` uchun `tmpfs` | 1 |
| Default seccomp profili (o'chirilmasin!) | 1 |
| ❌ **`docker.sock` hech qachon konteynerga mount qilinmaydi** | 1 |
| Rootless Podman yoki gVisor (`runsc`) | 3 |
| Kernel yangilanishi avtomatik (`unattended-upgrades`) | 1 |

### Resursni tugatish (resource exhaustion)
```
--memory=512m --memory-swap=512m   # swap = memory → swap'ga qochib ketmaydi
--cpus=0.5                          # cgroup v2 cpu.max
--pids-limit=256                    # fork bomba
--storage-opt size=2G               # XFS prjquota kerak
--ulimit nofile=1024:2048
```
⚠️ `--memory-swap` ni **albatta** `--memory` ga teng qiling. Aks holda
ilova swap'ni to'ldirib butun node'ni (shu bilan boshqa 40 mijozni) o'ldiradi.
Bu sizdagi Oracle micro serverlarida allaqachon sodir bo'lgan hodisa.

Disk: `overlay2` + XFS `prjquota` — `mkfs.xfs` paytida yoqilishi kerak,
keyin qo'shib bo'lmaydi. **Node o'rnatishda e'tiborga olinadi.**

### Kripto-mayning
Bepul tarifdagi birinchi muammo shu bo'ladi.
- Qattiq CPU cheklovi (0.25–0.5 vCPU) — mayning foydasiz bo'lib qoladi
- Bepul tarifda **doimiy 100% CPU** → avtomatik to'xtatish + ogohlantirish
- Mayning pool domenlariga chiquvchi ulanishni bloklash (DNS/nftables)
- Bepul tarif uchun **telefon yoki karta tasdiqlash** (eng samarali chora)

### Spam va phishing
- ⚠️ **Chiquvchi 25 / 465 / 587 portlarini boshidan bloklash.** Pochta
  kerak bo'lsa — faqat SMTP provayder orqali (Resend/SES API). Bu sizning
  IP diapazonini qora ro'yxatdan saqlaydi
- Deploy qilingan kontentni skanerlash (phishing shabloni, brend nomlari)
- `abuse@<brend>.uz` ishlaydigan pochta + 24 soat ichida javob tartibi
- Shartlarda (ToS) aniq taqiq va bir tomonlama o'chirish huquqi

### Chiquvchi hujum (bizning IP'dan DDoS)
- Chiquvchi trafik tezligini cheklash (tarifga qarab)
- **Private va metadata diapazonlarini bloklash:**
  `169.254.169.254` (cloud metadata — kalit o'g'irlash!), `10/8`,
  `172.16/12`, `192.168/16`, `127/8`
- Har ilovaga **alohida Docker network** — mijozlar bir-birini ko'rmaydi
- Provayder (Hetzner) abuse xabarini darhol qabul qilish tartibi

### Build vaqtidagi xatar
`npm install` ichida `postinstall` skripti — bu to'laqonli kod ishga tushishi.
- Build **alohida, bir martalik (ephemeral)** konteynerda
- Build konteyneri **registry va git'dan boshqa joyga chiqa olmaydi**
- Build vaqt chegarasi (10 daqiqa) va RAM chegarasi
- Build **hech qachon control node'da bo'lmaydi**
- Build keshini mijozlar o'rtasida **bo'lishmaslik** (kesh zaharlanishi)

### Platformaning o'zi
- SSH git server foydalanuvchiga **shell bermaydi** (`command=` majburiy,
  `no-pty,no-port-forwarding,no-agent-forwarding,no-X11-forwarding`)
- Registry: har ilovaga qisqa muddatli token, umumiy parol yo'q
- Control node'da foydalanuvchi kodi **nol**
- Agent faqat private network'da
- Sirlar: `.env` repo'da emas, `gitleaks` pre-commit, OAuth secret rotatsiyasi

## 4.2 Suiiste'molni oldini olish siyosati (mahsulot qarori)

Eng samarali himoya — **texnik emas, siyosiy**:

| Chora | Ta'sir |
|---|---|
| Bepul tarifda **faqat statik sayt** (konteyner yo'q) | Mayning va spam xatarini ~90% kesadi |
| Backend uchun **telefon raqam tasdiqlash** majburiy | Ko'pchilik suiiste'molchini to'xtatadi |
| Pulli tarif = karta/Payme bog'langan | Deyarli to'liq yechim |
| Yangi akkauntda birinchi 24 soat chegaralangan chiquvchi trafik | Hit-and-run hujumlarni to'xtatadi |

**Tavsiya:** bepul tarifda backend konteyner berish — kechiktirilsin yoki
telefon tasdiqlashga bog'lansin. Bu ro'yxatdan o'tish oqimiga ta'sir
qiladi, lekin platformaning omon qolishi shunga bog'liq.

## 4.3 Huquqiy tomon (O'zbekiston)

Bu bo'lim **yurist bilan tekshirilishi kerak** — quyidagilar faqat
e'tibor berish kerak bo'lgan nuqtalar ro'yxati:

- **Yuridik shaxs kerak.** Payme/Click/Uzum shartnomasi YaTT yoki MChJ
  talab qiladi. Buni **birinchi kundan** boshlash kerak — hujjatlar
  haftalar oladi va deploy kodiga parallel ketadi
- **Shaxsiy ma'lumotlar qonuni** — O'zbekiston rezidentlarining shaxsiy
  ma'lumotlari mamlakat ichida saqlanishi talabi bor. Mijozlarimiz
  ma'lumotlarini Germaniyada saqlashimiz — tekshirish kerak. Bu
  O'zbekistonda region ochish zaruratini tug'dirishi mumkin (01-hujjat, variant C)
- **Hosting provayder javobgarligi** — mijoz joylagan noqonuniy kontent
  uchun. ToS'da "xabar bo'lsa o'chiramiz" (notice-and-takedown) tartibi
  yozilishi kerak
- **Ommaviy oferta** va **maxfiylik siyosati** — saytda bo'lishi shart
- Soliq: xizmat ko'rsatishdan daromad, QQS holati

## 4.4 Monitoring va javob berish

| Nima | Qanday |
|---|---|
| Node holati | Uptime Kuma / Netdata, Telegram'ga ogohlantirish |
| Anomaliya (CPU 100% uzoq, trafik portlashi) | Metering jadvalidan avtomatik qoida |
| Xato kuzatuvi | Sentry (self-hosted yoki bepul tier) |
| Backup tekshiruvi | **Oyda bir marta tiklab ko'rish** — tekshirilmagan backup = backup yo'q |
| Incident jurnali | `docs/incidents/` — har uzilish yozib boriladi |

⚠️ **SLA bermang.** Yakka dasturchi 99.9% uptime majburiyatini bajara
olmaydi. "Best effort" deb yozing, kompensatsiya majburiyati olmang.

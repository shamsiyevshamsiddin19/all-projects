# Hetzner serverга botni chiqarish (deploy)

Bot 24/7 ishlashi va Instagram webhook'ni qabul qilishi uchun serverда
HTTPS manzil kerak. Meta faqat **haqiqiy SSL sertifikatли HTTPS** manzilni qabul qiladi.

Quyida to'liq, qadamma-qadam yo'riqnoma.

---

## 0. Nima kerak
- Hetzner serverга SSH orqali kira olish (sizда bor)
- Domen yoki bepul subdomen (masalan **duckdns.org** — bepul)
  > IP manzilning o'ziga Let's Encrypt sertifikat bermaydi, shuning uchun
  > domen kerak. duckdns.org da 2 daqiqада bepul subdomen olasiz.

---

## 1. Fayllarni serverga yuklash

Kompyuteringizdan (PowerShell), bot papkasidan:

```powershell
scp -r E:\instagram-bot root@SERVER_IP:/opt/instagram-bot
```

Yoki serverда git bilan tortib oling (agar GitHub'ga qo'ygan bo'lsangiz).

---

## 2. Serverга kirib, muhitni tayyorlash

```bash
ssh root@SERVER_IP

cd /opt/instagram-bot
apt update && apt install -y python3-venv python3-pip nginx

python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

`.env` fayl serverда borligini tekshiring (token'lar bilan).

---

## 3. systemd xizmatini o'rnatish

```bash
cp deploy/instagram-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now instagram-bot
systemctl status instagram-bot     # "active (running)" bo'lsa OK
```

Bot endi `127.0.0.1:5000` da ishlaydi (faqat server ichida).

---

## 4. Domenni serverга yo'naltirish

- **duckdns.org**: ro'yxatdan o'ting → subdomen yarating (masalan `shamsbot`) →
  IP maydoniga Hetzner server IP'sini yozing. Manzilingiz:
  `shamsbot.duckdns.org`
- Yoki o'z domeningizda **A record** yaratib, server IP'ga yo'naltiring.

---

## 5. Nginx + HTTPS (certbot)

```bash
# nginx configni qo'yish (ichidagi domenни o'zgartiring!)
cp deploy/nginx-instagram-bot.conf /etc/nginx/sites-available/instagram-bot
# domenni almashtiring:
sed -i 's/SIZNING_DOMEN.uz/shamsbot.duckdns.org/' /etc/nginx/sites-available/instagram-bot
ln -s /etc/nginx/sites-available/instagram-bot /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# HTTPS sertifikat (bepul, Let's Encrypt)
apt install -y certbot python3-certbot-nginx
certbot --nginx -d shamsbot.duckdns.org
```

Certbot avtomatik HTTPS'ga o'tkazadi. Endi manzilingiz:
`https://shamsbot.duckdns.org`

---

## 6. Meta'da Webhook ulash

Meta Developer → App → Instagram → **Webhooks**:
- **Callback URL**: `https://shamsbot.duckdns.org/webhook`
- **Verify token**: `.env` dagi `VERIFY_TOKEN` (masalan `mening_maxfiy_sozim_123`)
- **Subscribe**: `messages`, `comments`

Meta "Verified" desa — bot ishga tushdi! 🎉

---

## Tekshirish va loglar

```bash
# Bot ishlayaptimi
curl https://shamsbot.duckdns.org/
# -> "Instagram bot ishlayapti"

# Jonli loglar (kim yozdi, qanday javob berildi)
journalctl -u instagram-bot -f

# Botni qayta ishga tushirish (masalan .env o'zgartirsangiz)
systemctl restart instagram-bot
```

---

## Muammolarni hal qilish

| Muammo | Yechim |
|--------|--------|
| Webhook "verify failed" | `.env` dagi VERIFY_TOKEN Meta'dagi bilan bir xilmi? |
| 502 Bad Gateway | `systemctl status instagram-bot` — bot ishlayaptimi? |
| Javob kelmayapti | `journalctl -u instagram-bot -f` da xatoni qarang |
| Token muddati tugadi | Meta'dan yangi IGAA token olib, `.env` da yangilang, restart |

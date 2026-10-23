# Serverga joylash

Production: `/opt/wstore`, `wstore.service`. Nginx statik fayllarni `staticfiles/` dan oladi.

1. Baza va o'zgaradigan kod/config fayllarining zaxirasini oling; boshqa sessiya o'zgarishlari borligini solishtiring.
2. Faqat tasdiqlangan kod fayllarini yuboring. `.env`, bazalar, media, virtual muhit va zaxiralar sinxronlanmaydi.
3. `python manage.py check --deploy`, `python manage.py migrate --check`, `python manage.py collectstatic --noinput` bajariladi.
4. EN/RU `.po` yangilansa `.mo` ham qayta kompilyatsiya qilinadi (`manage.py compilemessages`, GNU gettext talab qilinadi; muqobil: polib).
5. HTTPS nginx server blokiga `nginx-private-media.conf` dagi location qoidasini qo'shing; `nginx -t` va reload bajaring.
6. `systemctl restart wstore` statik fayllar versiyasini ham yangilaydi. Yangi `?v=` bilan CSS/JS, katalog, mahsulot, auth redirect va yopiq media yo'lini tekshiring.

Rollback: shu deploydan oldingi kod/nginx zaxirasini qaytaring, collectstatic va restart/reload bajaring. Kod rollback uchun ishlab turgan bazani eski nusxaga almashtirmang.

## Click

`CLICK_SECRET_KEY` — Click bergan direct Shop API kaliti. `CLICK_BRIDGE_SECRET` — faqat tashqi bridge bo'lsa, o'sha servis bilan kelishilgan tasodifiy kalit. Ular Git'ga kiritilmaydi. Hech biri sozlanmasa to'lov xavfsiz yopiq turadi.

Haqiqiy checkout uchun mahsulot ACTIVE, arxiv mavjud va to'lov kaliti sozlangan bo'lishi kerak. Arxiv uchun dastur chegarasi 40 MiB, nginx so'rov chegarasi 50 MiB.

# 📝 Python: String Metodlari va RegEx (Mukammal Qo'llanma)

Ushbu qo'llanmada matnlar bilan ishlashning eng kuchli vositalari: Python'ning ichki String metodlari va **RegEx (Regular Expressions)** haqida to'liq va sodda tarzda o'rganamiz. Bu ayniqsa botlar yozganda foydalanuvchi ma'lumotlarini (ism, telefon, email) tekshirish (validation) uchun juda kerak!

---

## 🛠 1. String Metodlari (Matn bilan ishlash)

Python'da matn (`str`) obyektlari uchun juda ko'p tayyor funksiyalar (metodlar) mavjud. Ularni o'rganish matn tahlilining yarmini hal qiladi.

### Asosiy metodlar:

#### 1. `.split()` va `.join()` - Ajratish va Birlashtirish
**Nimaga kerak?** 
- `.split()` funksiyasi bitta butun matnni qandaydir belgi (masalan, vergul yoki probel) orqali kesib, ro'yxat (list) ko'rinishiga keltirib beradi.
- `.join()` esa buning teskarisi: ro'yxat ichidagi so'zlarni bitta belgi (masalan, chiziqcha) orqali ulab, bitta butun matnga aylantiradi.

```python
matn = "olma, banan, uzum"

# Vergul va bo'sh joy orqali matnni 3 ta qismga bo'lamiz
mevalar = matn.split(", ")
print(mevalar)  # Natija: ['olma', 'banan', 'uzum']

# Endi ro'yxatdagi so'zlarni " | " belgisi bilan biriktiramiz
yangi_matn = " | ".join(mevalar)
print(yangi_matn) # Natija: "olma | banan | uzum"
```

#### 2. `.strip()` - Chetlarini tozalash
**Nimaga kerak?** Foydalanuvchilar ba'zida so'zning boshida yoki oxirida adashib bo'sh joy (probel) yoki enter bosib yuborishadi. `.strip()` aynan shu ortiqcha bo'shliq va enterlarni olib tashlab, matnning o'zini toza holatda saqlab qoladi.

```python
xabar = "   Salom bot!   "

# Matnning ikki chetidagi keraksiz bo'shliqlarni tozalash
toza = xabar.strip()
print(toza)  # Natija: "Salom bot!"
```

#### 3. `.replace()` - O'zgartirish (Almashtirish)
**Nimaga kerak?** Matn ichidagi qaysidir ma'lum bir so'zni topib, uning o'rniga boshqa so'z qo'yish uchun ishlatiladi.

```python
matn = "Men Javascript'ni yaxshi ko'raman."

# "Javascript" so'zini "Python" ga o'zgartirish
yangi = matn.replace("Javascript", "Python")
print(yangi) # "Men Python'ni yaxshi ko'raman."
```

#### 4. Katta-kichik harflar va Qidirish (Validation uchun)
**Nimaga kerak?** 
- `.capitalize()` — Matnning faqat birinchi harfini katta qiladi (masalan ismlarni chiroyli chiqarish uchun).
- `.upper()` — Matndagi hamma harflarni kattalashtiradi.
- `.startswith()` — Matn ma'lum bir so'z bilan boshlanganligini tekshiradi (True yoki False qaytaradi).
- `.endswith()` — Matn ma'lum bir so'z bilan tugaganligini tekshiradi.
- `in` — Biror so'z matnning qayeridadir qatnashganligini tekshiradi.

```python
ism = "ali"

# Katta va kichik harflar
print(ism.capitalize()) # Natija: "Ali" (Faqat 1-harf katta)
print(ism.upper())      # Natija: "ALI" (Hammasi katta)

# Tekshirish metodlari
matn = "Assalomu alaykum do'stlar"

print(matn.startswith("Assalom")) # True (Matn "Assalom" bilan boshlangan)
print(matn.endswith("hayr"))      # False (Matn "hayr" bilan tugamagan)
print("alaykum" in matn)          # True ("alaykum" so'zi matn ichida bor)
```

---

## 🚀 2. RegEx (Regular Expressions) - Doimiy ifodalar

Oddiy string metodlari yetarli bo'lmaganda (masalan: "Matn to'liq ismmi?", "Faqat telefon raqammi?" yoki "Bu haqiqiy emailmi?") **RegEx** yordamga keladi. U matnning ma'lum bir tuzilishga (qolipga) mos kelishini tekshiradi. Pythonda uning uchun `re` kutubxonasi mavjud.

### 🔑 RegEx dagi maxsus belgilar (Qolip belgilari)
- `\d` - Har qanday bitta raqam (0-9)
- `\D` - Raqam bo'lmagan har qanday bitta belgi
- `\w` - Bitta harf, raqam yoki tagchiziq (`_`)
- `\s` - Bitta bo'sh joy (probel, enter, tab)
- `^` - Qidiruvni aynan matnning eng boshidan boshlash
- `$` - Qidiruvni aynan matnning oxirida tugatish
- `+` - Bitta yoki undan ko'p marta kelishi mumkin (masalan: `\d+` = qator kelgan bir nechta raqamlar)
- `{N}` - Aynan N marta takrorlanishi (`\d{4}` = aynan 4 ta raqam bo'lishi shart)
- `[...]` - Qavs ichidagi istalgan bitta belgi (masalan: `[a-z]` = faqat kichik harflar)

---

### 🔍 Asosiy `re` metodlari

#### 1. `re.match()` - Matn boshini tekshirish
**Nimaga kerak?** Berilgan qolip matnning aynan **boshida** kelyaptimi yoki yo'qmi, shuni tekshiradi. Agar topilsa moslikni qaytaradi, topilmasa `None`.

```python
import re

matn = "+998901234567 bu raqamim"

# ^\+998\d{9} qolipi nima deydi:
# ^      -> Matn boshi
# \+998  -> Aynan +998 (Plyusni qochirish uchun oldiga \ qoydik)
# \d{9}  -> Va orqasidan aynan 9 ta raqam
natija = re.match(r"^\+998\d{9}", matn)

if natija:
    print("O'xshadi!", natija.group()) # "+998901234567" qismini ushlab oldi
else:
    print("O'xshamadi")
```

#### 2. `re.search()` - Matnning istalgan joyidan qidirish
**Nimaga kerak?** `re.match()` ga o'xshaydi, lekin u nafaqat matn boshini, balki matnning o'rtasi va oxirini ham qidirib chiqadi. Qolipga mos tushgan eng birinchi qismni topishi bilan to'xtaydi.

```python
matn = "Mening raqamim +998997776655. Bemalol qo'ng'iroq qiling."

# Raqam matn boshida emas, o'rtasida kelyapti. Shuning uchun search() ishlatamiz.
qidiruv = re.search(r"\+998\d{9}", matn)
print(qidiruv.group()) # Natija: "+998997776655"
```

#### 3. `re.findall()` - Barchasini topib ro'yxat qilish
**Nimaga kerak?** Matn ichida qolipga tushadigan qismlar bir nechta bo'lishi mumkin. `.findall()` barchasini izlab topadi va bitta tayyor List (ro'yxat) qilib beradi.

```python
matn = "1-noyabrda 500 ming, 2-sanasida esa 120000 som pul tushdi."

# \d+ qolipi: Har qanday uzunlikdagi raqamlar ketma-ketligini top
sonlar = re.findall(r"\d+", matn)
print(sonlar) # Natija: ['1', '500', '2', '120000']
```

#### 4. `re.sub()` - Matnni qolip orqali almashtirish
**Nimaga kerak?** Bu huddi stringdagi `.replace()` metodining kuchaytirilgan versiyasi. `.replace()` faqat aniq bitta so'zni o'zgartirsa, `.sub()` butun boshli naqshlarni (masalan: barcha raqamlarni yoki barcha harflarni) boshqa narsaga o'zgartirib bera oladi.

```python
matn = "Mening ismim Ali. Men 25 yoshman."

# Matndagi barcha raqamlar ketma-ketligini (\d+) "[YASHIRILGAN]" so'ziga almashtiramiz
yashirin = re.sub(r"\d+", "[YASHIRILGAN]", matn)
print(yashirin) # Natija: "Mening ismim Ali. Men [YASHIRILGAN] yoshman."
```

---

## 🎯 3. Amaliy Validatsiyalar (Tayyor Patternlar)

Telegram bot yoki dasturlarda foydalanuvchi kiritgan ma'lumotlarni xatosiz ekanligini tasdiqlash (validation) uchun tayyor naqshlar:

### 1. Telefon raqamni tekshirish (O'zbekiston formati)
**Tushuntirish:** Raqam +998 bilan boshlanishi va jami yana 9 ta raqam bo'lishi shartligini tekshiramiz. `^` va `$` yordamida matn to'liq shu qolip ichida qolishiga erishamiz, yonida harflar aralashib qolishini taqiqlaymiz.

```python
import re

def is_phone(text):
    # ^\+998 = +998 bilan boshlanadi
    # [0-9]{9} = Orqasidan aynan 9 ta raqam keladi
    # $ = Shu yerda matn tugaydi
    pattern = r"^\+998[0-9]{9}$" 
    return bool(re.match(pattern, text))

print(is_phone("+998901112233")) # True
print(is_phone("Salom +998901112233")) # False (Yozuvlar bor, $ qoidasi buzildi)
print(is_phone("998901112233")) # False (+ belgisi yo'q)
```

### 2. Email (Elektron pochta) tekshirish
**Tushuntirish:** Elektron pochta qoidasi: Ism qismi, keyin `@` belgisi, keyin domen nomi va `.com` yoki `.uz` kabi qismlardan iborat bo'lishini tekshiradi.

```python
def is_email(text):
    # Harflar, raqamlar va belgilar ketma-ketligi -> @ -> Harflar va raqamlar -> . -> Harflar
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, text))

print(is_email("admin@example.com")) # True
print(is_email("admin.com")) # False (Chunki @ belgisi yo'q)
```

### 3. Matn faqat harflardan iboratmi? (Ismni tekshirish)
**Tushuntirish:** Ba'zida foydalanuvchi ismini so'raganimizda, ular raqam yoki xar-xil emojilar qo'shib yuboradi. Ushbu tekshiruv faqat Lotin harflari va bo'sh joy (probel) bo'lishinini talab qiladi.

```python
def is_name(text):
    # [a-zA-Z] = Barcha Lotin harflari (katta va kichik)
    # \s = Bo'sh joy (misol uchun familiya qo'shib yozilganda kerak)
    pattern = r"^[a-zA-Z\s]+$"
    return bool(re.match(pattern, text))

print(is_name("Abdulla")) # True
print(is_name("Ali Valiyev")) # True (O'rtada bo'sh joy ruxsat etilgan)
print(is_name("Ali 123")) # False (123 raqamlari mumkin emas)
```

### 4. Havola (Link / URL) tekshirish
**Tushuntirish:** Matnning veb-sayt manzili (URL) formatida ekanligini tekshiradi. Boshida "http", "https" yoki "www" qismlari ishtirok etishi ham nazarda tutilgan.

```python
def is_url(text):
    pattern = r"^(https?://)?(www\.)?([a-zA-Z0-9-]+)\.[a-zA-Z]{2,}(/.*)?$"
    return bool(re.match(pattern, text))

print(is_url("https://kun.uz")) # True
print(is_url("yandex.ru/maps")) # True
print(is_url("kunuz")) # False (Nuqta yo'q)
```

---

## 💡 Maslahatlar
1. Agar ma'lumotni tozalash oson bo'lsa, har doim ham `RegEx` ishlatavermang. Oddiy `.replace()` yoki `.split()` dan foydalanish kodni o'qishni va tushunishni osonlashtiradi hamda tezroq ishlaydi.
2. `RegEx` qoliplarini Pythonda doimo `r"..."` (Raw string - Xom matn) shaklida yozishni unutmang. Aks holda `\n` yoki boshqa maxsus belgilar oddiy qochirish belgisi sifatida o'qilib qolib, xatolik yuzaga kelishi mumkin.
3. Katta loyihalarda Regex ishlatishdan oldin **https://regex101.com/** saytida qolipingizni sinab ko'ring. Bu sayt siz yozgan RegEx qanday ishlashini bitta-bitta ajratib, rangli tushuntirib beradi!

# Python darsligi — Barcha mavzular (to'liq, 7 bo'lim, 28 dars)

_Ushbu darslik noldan (Python nima ekanidan) tortib, professional darajadagi OOP, testlash va CLI loyiha qurishgacha bo'lgan to'liq yo'lni qamrab oladi. Daraja pastdan yuqoriga: 00-bob → 06-bob. Barcha terminal buyruqlari **Ubuntu** (Debian-asosidagi distributivlar) uchun moslashtirilgan. Mavzular ketma-ketligi va tarkibi 2025-2026-yillardagi joriy Python (3.12+, jumladan 3.13/3.14 yangiliklari) va zamonaviy vositalar (`uv`) bo'yicha tadqiqot asosida tuzilgan._

---

## 00-BOB — Kirish

| № | Mavzu | Fayl |
|---|---|---|
| 0.1 | Python nima, tarixi va o'rnatish (Ubuntu) | 0.1-python-nima-ornatish.md |
| 0.2 | Birinchi dastur, REPL va kod uslubi (PEP 8, Zen of Python) | 0.2-birinchi-dastur-repl-kod-uslubi.md |

## 01-BOB — Sintaksis asoslari

| № | Mavzu | Fayl |
|---|---|---|
| 1.1 | O'zgaruvchilar, ma'lumot turlari va operatorlar | 1.1-ozgaruvchilar-turlar-operatorlar.md |
| 1.2 | Kirish/chiqish va f-string | 1.2-kirish-chiqish-fstring.md |
| 1.3 | Shart operatorlari (if/elif/else, walrus, match-case) | 1.3-shart-operatorlari.md |
| 1.4 | Sikllar (for/while/range/break/continue/else) | 1.4-sikllar.md |

## 02-BOB — Ma'lumot tuzilmalari

| № | Mavzu | Fayl |
|---|---|---|
| 2.1 | Satrlar (strings) bilan ishlash | 2.1-satrlar.md |
| 2.2 | Ro'yxatlar (list) va Tuple | 2.2-royxatlar-tuple.md |
| 2.3 | Lug'atlar (dict) va Set | 2.3-lugatlar-set.md |
| 2.4 | Comprehensions (list, dict, set) | 2.4-comprehensions.md |
| 2.5 | Qaysi tuzilmani qachon tanlash + mini-loyiha (Kutubxona katalogi) | 2.5-tuzilma-tanlash-mini-loyiha.md |

## 03-BOB — Funksiyalar va modullar

| № | Mavzu | Fayl |
|---|---|---|
| 3.1 | Funksiyalar, argumentlar va lambda | 3.1-funksiyalar-argumentlar-lambda.md |
| 3.2 | Scope, closures va rekursiya | 3.2-scope-closures-rekursiya.md |
| 3.3 | Modullar, paketlar va standart kutubxona | 3.3-modullar-paketlar-standart-kutubxona.md |
| 3.4 | Virtual muhit va paket boshqaruvi (pip, uv) | 3.4-virtual-muhit-paket-boshqaruv.md |

## 04-BOB — OOP (Obyektga yo'naltirilgan dasturlash)

| № | Mavzu | Fayl |
|---|---|---|
| 4.1 | Klass va obyekt asoslari | 4.1-klass-obyekt-asoslari.md |
| 4.2 | Meros (inheritance) va super() | 4.2-meros-super.md |
| 4.3 | Inkapsulyatsiya, property va polimorfizm | 4.3-inkapsulyatsiya-property-polimorfizm.md |
| 4.4 | Magic metodlar, dataclasses va Enum | 4.4-magic-metodlar-dataclasses-enum.md |
| 4.5 | Abstract classes (abc moduli) | 4.5-abstract-classes.md |

## 05-BOB — Istisnolar, fayllar va generatorlar

| № | Mavzu | Fayl |
|---|---|---|
| 5.1 | Istisnolar (exceptions) | 5.1-istisnolar.md |
| 5.2 | Fayllar (matn/JSON/CSV) va context managerlar | 5.2-fayllar-context-managers.md |
| 5.3 | Iteratorlar va generatorlar | 5.3-iteratorlar-generatorlar.md |
| 5.4 | Dekoratorlar | 5.4-dekoratorlar.md |
| 5.5 | Type hints (tur maslahatlari) | 5.5-type-hints.md |

## 06-BOB — Ilg'or va professional mavzular

| № | Mavzu | Fayl |
|---|---|---|
| 6.1 | Asyncio va concurrency (threading/multiprocessing/GIL) | 6.1-asyncio-concurrency.md |
| 6.2 | Testlash (pytest) va loglash | 6.2-testlash-pytest-loglash.md |
| 6.3 | Paketlash, uv va yakuniy CLI loyiha (Vazifa boshqaruvchi) | 6.3-paketlash-uv-yakuniy-cli-loyiha.md |

---

## Umumiy ma'lumot

- **00-bob (0.1-0.2):** Kirish — Python tarixi, joriy versiyalar (3.14/3.13, kurs 3.12+ asos qilingan), Ubuntu'da o'rnatish (`apt`, `python3`/`pip3`, `deadsnakes` PPA), IDE (`snap install code`/`pycharm-community`), venv, REPL, PEP 8, Zen of Python.
- **01-bob (1.1-1.4):** Sintaksis asoslari — o'zgaruvchilar, turlar, operatorlar, f-string, `if`/`elif`/`else`, walrus operator (`:=`), `match`/`case`, `for`/`while` sikllari, `range()`, `break`/`continue`.
- **02-bob (2.1-2.5):** Ma'lumot tuzilmalari — satrlar (slicing, metodlar), ro'yxat va tuple (mutable/immutable), lug'at va set (hash asosida tezlik), comprehensions, tuzilma tanlash mezonlari + "Kutubxona katalogi" mini-loyihasi.
- **03-bob (3.1-3.4):** Funksiyalar va modullar — `*args`/`**kwargs`, lambda, scope/`global`/`nonlocal`, closures, rekursiya, `import` turlari, `__name__ == "__main__"`, standart kutubxona (`math`, `random`, `datetime`, `os`, `json`, `collections`), `pip`/`venv` va zamonaviy `uv` paket menejeri.
- **04-bob (4.1-4.5):** OOP — klass/obyekt, `__init__`/`self`, meros va `super()`, `@property`, inkapsulyatsiya konvensiyalari, polimorfizm va duck typing, magic metodlar (`__str__`, `__eq__`, `__add__`), `@dataclass`, `Enum`, abstrakt klasslar (`abc`, `@abstractmethod`).
- **05-bob (5.1-5.5):** Istisnolar, fayllar, generatorlar — `try`/`except`/`else`/`finally`, maxsus istisno klasslari, `with`/context managerlar, JSON/CSV fayllar, iteratorlar, `yield`/`yield from`, dekoratorlar (`@wraps`, `@lru_cache`, argumentli dekoratorlar), type hints (`list[int]`, `X | None`, `mypy`).
- **06-bob (6.1-6.3):** Ilg'or mavzular — GIL, `threading`/`multiprocessing`/`asyncio` taqqoslashi, `async`/`await`, `pytest` (fixture, parametrize), `logging`, professional loyiha strukturasi, `argparse`, `pyproject.toml`, yakuniy "Vazifa boshqaruvchi" CLI loyihasi.
- **Jami: 28 dars** (0.1 va 0.2 dan 6.3 gacha), noldan professional darajadagi Python dasturchisi bo'lishgacha to'liq qamrab olingan.
- Har bir dars bir xil tuzilmaga ega: **Bu darsda nimalarni o'rganasiz** → **Nazariy qism** → **Amaliy misol** → **Keng tarqalgan xatolar** (har biri ❌/✅ va SABAB bilan) → **Mashq/topshiriq** (Oson/O'rtacha/Qiyin, javoblari bilan) → **Qisqacha xulosa**.
- Barcha terminal buyruqlari Ubuntu (apt, `python3`/`pip3`, `snap`) uchun moslashtirilgan; zamonaviy `uv` paket menejeri alohida (3.4-dars) va yakuniy loyihada (6.3-dars) tanishtirilgan, an'anaviy `pip`+`venv` bilan bir qatorda.

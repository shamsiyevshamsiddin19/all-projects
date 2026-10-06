from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    bot_username: str = field(default_factory=lambda: os.getenv("BOT_USERNAME", "talabaxizmatlaribot"))

    admin_ids: list[int] = field(default_factory=list)
    admin_user: str = field(default_factory=lambda: os.getenv("ADMIN_USER", "admin"))
    admin_password: str = field(default_factory=lambda: os.getenv("ADMIN_PASSWORD", ""))
    # Yordam bo'limidagi qo'llab-quvvatlash kontakti (masalan: @username)
    admin_contact: str = field(default_factory=lambda: os.getenv("ADMIN_CONTACT", ""))

    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))

    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))

    claude_model: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"))
    claude_model_premium: str = field(default_factory=lambda: os.getenv("CLAUDE_MODEL_PREMIUM", "claude-opus-4-6"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # Marketing / o'sish
    welcome_bonus: int = field(default_factory=lambda: _int("WELCOME_BONUS", 5000))
    cashback_pct: int = field(default_factory=lambda: _int("CASHBACK_PCT", 4))
    # Web search (haqiqiy manbalar) — 0 qilib o'chirish mumkin
    web_search: int = field(default_factory=lambda: _int("WEB_SEARCH", 1))

    # VIP foydalanuvchilar — barcha hujjatlar bitta maxsus narxda
    vip_ids: list[int] = field(default_factory=list)
    vip_price: int = field(default_factory=lambda: _int("VIP_PRICE", 1000))

    # Pexels — slaydlar uchun mavzuga mos fon-foto (bo'sh bo'lsa, shunchaki ishlatilmaydi)
    pexels_api_key: str = field(default_factory=lambda: os.getenv("PEXELS_API_KEY", ""))

    click_service_id: str = field(default_factory=lambda: os.getenv("CLICK_SERVICE_ID", "99657"))
    click_merchant_id: str = field(default_factory=lambda: os.getenv("CLICK_MERCHANT_ID", "59136"))
    click_secret_key: str = field(default_factory=lambda: os.getenv("CLICK_SECRET_KEY", ""))
    click_merchant_user_id: str = field(default_factory=lambda: os.getenv("CLICK_MERCHANT_USER_ID", "81435"))
    click_return_url: str = field(default_factory=lambda: os.getenv("CLICK_RETURN_URL", ""))
    # Ko'prik (myxvest PHP) shu prefiks bilan boshlanadigan to'lovlarni shu botga uzatadi.
    # Barcha to'lovlar: MUST<payment_id> (buyurtma yoki balans — order_id orqali ajratiladi)
    click_tx_prefix: str = field(default_factory=lambda: os.getenv("CLICK_TX_PREFIX", "MUST"))
    bridge_secret: str = field(default_factory=lambda: os.getenv("BRIDGE_SECRET", ""))

    web_host: str = field(default_factory=lambda: os.getenv("WEB_HOST", "127.0.0.1"))
    web_port: int = field(default_factory=lambda: _int("WEB_PORT", 8092))
    public_base_url: str = field(default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://141.147.156.65/mustaqil"))

    tmp_dir: str = field(default_factory=lambda: os.getenv("TMP_DIR", "/tmp/mustaqilbot"))
    min_topup: int = field(default_factory=lambda: _int("MIN_TOPUP", 10000))

    # Narxlar (so'm)
    price_tezis: int = field(default_factory=lambda: _int("PRICE_TEZIS", 10000))
    price_mustaqil: int = field(default_factory=lambda: _int("PRICE_MUSTAQIL", 15000))
    price_referat: int = field(default_factory=lambda: _int("PRICE_REFERAT", 20000))
    price_krasword: int = field(default_factory=lambda: _int("PRICE_KRASWORD", 15000))
    price_maqola: int = field(default_factory=lambda: _int("PRICE_MAQOLA", 25000))
    price_slayd: int = field(default_factory=lambda: _int("PRICE_SLAYD", 25000))
    price_kurs: int = field(default_factory=lambda: _int("PRICE_KURS", 50000))
    price_diplom: int = field(default_factory=lambda: _int("PRICE_DIPLOM", 100000))

    # Referal bonuslar (so'm)
    ref_tezis: int = field(default_factory=lambda: _int("REF_BONUS_TEZIS", 1000))
    ref_mustaqil: int = field(default_factory=lambda: _int("REF_BONUS_MUSTAQIL", 1500))
    ref_referat: int = field(default_factory=lambda: _int("REF_BONUS_REFERAT", 2000))
    ref_krasword: int = field(default_factory=lambda: _int("REF_BONUS_KRASWORD", 1500))
    ref_maqola: int = field(default_factory=lambda: _int("REF_BONUS_MAQOLA", 2000))
    ref_slayd: int = field(default_factory=lambda: _int("REF_BONUS_SLAYD", 1500))
    ref_kurs: int = field(default_factory=lambda: _int("REF_BONUS_KURS", 5000))
    ref_diplom: int = field(default_factory=lambda: _int("REF_BONUS_DIPLOM", 8000))

    def __post_init__(self):
        raw = os.getenv("ADMIN_IDS", "")
        self.admin_ids = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]
        raw_vip = os.getenv("VIP_IDS", "")
        self.vip_ids = [int(x.strip()) for x in raw_vip.split(",") if x.strip().isdigit()]

    # ─── Dinamik narx: sahifa soniga × token-asosli tarif ───

    def per_unit(self, doc_type: str) -> int:
        """1 bet/slayd/so'z uchun narx (token sarfini aks ettiradi)."""
        d = DOC_TYPES.get(doc_type, {})
        return _overrides.get(f"perunit_{doc_type}", d.get("per_unit", 2000))

    def min_price(self, doc_type: str) -> int:
        """Eng kam narx (kam sahifali ish ham shu narxdan kam bo'lmaydi)."""
        d = DOC_TYPES.get(doc_type, {})
        return _overrides.get(f"minprice_{doc_type}", d.get("min_price", 10000))

    def price_for(self, doc_type: str, count: int) -> int:
        """Buyurtma narxi = max(min_narx, 1 bet narxi × sahifa soni)."""
        return max(self.min_price(doc_type), self.per_unit(doc_type) * max(1, int(count)))

    def is_vip(self, user_id: int) -> bool:
        return user_id in self.vip_ids

    def eff_vip_price(self) -> int:
        return _overrides.get("vip_price", self.vip_price)

    def price_for_user(self, user_id: int, doc_type: str, count: int) -> int:
        """VIP foydalanuvchiga maxsus narx, qolganlarga oddiy hisob."""
        if self.is_vip(user_id):
            return self.eff_vip_price()
        return self.price_for(doc_type, count)

    def price(self, doc_type: str) -> int:
        """\"...dan\" ko'rsatkichi uchun — eng kam narx."""
        return self.min_price(doc_type)

    def ref_bonus(self, doc_type: str) -> int:
        k = f"ref_{doc_type}"
        return _overrides.get(k, getattr(self, k, 3000))

    def eff_min_topup(self) -> int:
        return _overrides.get("min_topup", self.min_topup)

    def maintenance(self) -> bool:
        return bool(_overrides.get("maintenance", 0))

    def eff_welcome_bonus(self) -> int:
        return _overrides.get("welcome_bonus", self.welcome_bonus)

    def eff_cashback_pct(self) -> int:
        return _overrides.get("cashback_pct", self.cashback_pct)

    def premium_mult(self) -> float:
        """Premium narx koeffitsienti (foizda saqlanadi: 200 = 2.0x)."""
        return _overrides.get("premium_pct", 200) / 100.0

    def web_search_on(self) -> bool:
        return bool(_overrides.get("web_search", self.web_search))


# Admin paneldan o'rnatilgan jonli sozlamalar (DB settings jadvalidan).
# main.py startda yuklaydi; admin saqlaganda yangilanadi → restart shart emas.
_overrides: dict[str, int] = {}


def apply_overrides(data: dict) -> None:
    _overrides.clear()
    for k, v in (data or {}).items():
        try:
            _overrides[k] = int(v)
        except (ValueError, TypeError):
            pass


settings = Settings()

# Har ish: birlik (unit), sahifa oralig'i (cmin/cmax/cdef), 1 birlik narxi
# (per_unit — token sarfiga mos), eng kam narx (min_price), qisqacha qoida (desc).
DOC_TYPES = {
    "tezis": {
        "emoji": "📋", "label": "Tezis", "format": "docx",
        "unit": "bet", "cmin": 2, "cmax": 6, "cdef": 3,
        "per_unit": 2000, "min_price": 4000,
        "desc": ("Ilmiy konferentsiya uchun qisqa ish. Tarkibi: annotatsiya, "
                 "kalit so'zlar, kirish, asosiy natijalar, xulosa, 3-5 manba.\n"
                 "📐 Qoida: 1-3 bet, ixcham va aniq, faqat eng muhim natijalar."),
    },
    "mustaqil": {
        "emoji": "📝", "label": "Mustaqil ish", "format": "docx",
        "unit": "bet", "cmin": 6, "cmax": 20, "cdef": 10,
        "per_unit": 900, "min_price": 5400,
        "desc": ("Talaba mustaqil bajaradigan ish. Tarkibi: kirish, asosiy qism "
                 "(2-3 bo'lim), xulosa, 5+ manba.\n"
                 "📐 Qoida: 5-10 bet, fan o'qituvchisi talabiga mos."),
    },
    "referat": {
        "emoji": "📄", "label": "Referat", "format": "docx",
        "unit": "bet", "cmin": 8, "cmax": 35, "cdef": 12,
        "per_unit": 800, "min_price": 6400,
        "desc": ("Mavzu bo'yicha to'liq sharh. Tarkibi: mundarija, kirish, asosiy "
                 "qism (3-4 bo'lim), xulosa, 10+ manba (APA).\n"
                 "📐 Qoida: 10-15 bet, Times New Roman 14, 1.5 interval."),
    },
    "maqola": {
        "emoji": "📰", "label": "Ilmiy maqola", "format": "docx",
        "unit": "bet", "cmin": 6, "cmax": 25, "cdef": 8,
        "per_unit": 1000, "min_price": 6000,
        "desc": ("Ilmiy jurnal uchun maqola. Tarkibi: UDK, annotatsiya, kalit "
                 "so'zlar, kirish, metodologiya, natijalar, xulosa, adabiyotlar (GOST).\n"
                 "📐 Qoida: 5-15 bet, ilmiy uslub, manbalar bilan."),
    },
    "slayd": {
        "emoji": "📊", "label": "Slayd (taqdimot)", "format": "pptx",
        "unit": "slayd", "cmin": 8, "cmax": 40, "cdef": 14,
        "per_unit": 500, "min_price": 4000,
        "desc": ("PowerPoint taqdimot (PPTX). Har slaydda sarlavha + 4-6 nuqta, "
                 "muqova va xulosa slaydlari bilan.\n"
                 "📐 Qoida: 10-20 slayd, mavzuga mos, mantiqiy ketma-ketlik."),
    },
    "kurs": {
        "emoji": "📚", "label": "Kurs ishi", "format": "docx",
        "unit": "bet", "cmin": 20, "cmax": 65, "cdef": 30,
        "per_unit": 750, "min_price": 15000,
        "desc": ("To'liq kurs ishi. Tarkibi: mundarija, kirish, 3 bob (nazariy, "
                 "tahliliy, takliflar), xulosa, 20+ manba, ilovalar.\n"
                 "📐 Qoida: 25-40 bet, ilmiy rahbar talabiga mos."),
    },
    "diplom": {
        "emoji": "🎓", "label": "Diplom ishi", "format": "docx",
        "unit": "bet", "cmin": 45, "cmax": 100, "cdef": 60,
        "per_unit": 700, "min_price": 31500,
        "desc": ("Bitiruv malakaviy ishi (BMI). Tarkibi: annotatsiya, mundarija, "
                 "kirish, 3 bob, xulosa, 30+ manba (GOST), ilovalar.\n"
                 "📐 Qoida: 50-80 bet, to'liq ilmiy apparat bilan."),
    },
    "krasword": {
        "emoji": "🎯", "label": "Krossvord", "format": "png+docx",
        "unit": "so'z", "cmin": 15, "cmax": 60, "cdef": 25,
        "per_unit": 250, "min_price": 3750,
        "desc": ("Mavzu bo'yicha krossvord (PNG rasm + DOCX). So'zlar va tariflar.\n"
                 "📐 Qoida: 20-40 so'z, 3-12 harf, mavzuga oid."),
    },
}

LANGS = {"uz": "O'zbek", "ru": "Rus", "en": "Ingliz"}

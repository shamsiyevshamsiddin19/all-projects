from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Category, Product

User = get_user_model()

CATEGORIES_DATA = [
    {"name": "Botlar", "slug": "bot", "icon": "bot"},
    {"name": "Saytlar", "slug": "website", "icon": "globe"},
    {"name": "Ilovalar", "slug": "app", "icon": "smartphone"},
    {"name": "Kod bloklari", "slug": "code", "icon": "puzzle"},
    {"name": "UI kitlar", "slug": "uikit", "icon": "palette"},
]

PRODUCTS_DATA = [
    {
        "title": "Telegram Do'kon Boti",
        "slug": "telegram-shop-bot",
        "price": Decimal("29.00"),
        "category_slug": "bot",
        "subcategory": None,
        "badge": "TOP SOTUV",
        "tech_stack": ["Python", "Telegram"],
        "features": [
            "Aiogram 3 framework asosida qurilgan",
            "Click va Payme integratsiyasi tayyor",
            "Katalog, savatcha va buyurtma boshqaruvi",
            "Oson sozlanuvchi admin panel"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1611746872915-64382b5c76da?w=800&q=80",
        "rating": 4.8,
        "sales_count": 214,
        "telegram_username": "devbek",
        "description": "Telegram orqali tovar va xizmatlarni avtomatlashtirilgan tarzda sotish uchun to'liq professional bot. Admin orqali yangi tovar qo'shish, statistika ko'rish va buyurtmalarni boshqarish mumkin."
    },
    {
        "title": "Next.js E-commerce Sayt",
        "slug": "nextjs-ecommerce",
        "price": Decimal("99.00"),
        "category_slug": "website",
        "subcategory": "other",
        "badge": "YANGI",
        "tech_stack": ["Next.js", "React", "TailwindCSS"],
        "features": [
            "Next.js App Router va Server Components",
            "To'liq TailwindCSS dark/light tema",
            "SEO optimallashtirilgan tezkor sahifalar",
            "Prisma va PostgreSQL ulanishi tayyor"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1467232004584-a241de8bcf5d?w=800&q=80",
        "rating": 4.9,
        "sales_count": 87,
        "telegram_username": "uxmaster",
        "description": "Eng so'nggi zamonaviy talablarga javob beradigan to'liq onlayn do'kon platformasi. Mahsulotlar katalogi, filterlar, buyurtma berish va to'lov oqimi mavjud."
    },
    {
        "title": "Flutter Yetkazib berish ilovasi",
        "slug": "flutter-delivery-app",
        "price": Decimal("149.00"),
        "category_slug": "app",
        "subcategory": None,
        "badge": None,
        "tech_stack": ["Flutter"],
        "features": [
            "Android va iOS uchun yagona kod bazasi",
            "Xaritada real vaqtda kuryerni kuzatish",
            "Toza arxitektura (Clean Architecture & BLoC)",
            "Ko'p tilli interfeys (UZ, RU, EN)"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&q=80",
        "rating": 5.0,
        "sales_count": 42,
        "telegram_username": "mobiuz",
        "description": "Restoran va do'konlar uchun mo'ljallangan qulay kuryerlik yetkazib berish mobil ilovasi. Mijoz va kuryer rejimlari mavjud."
    },
    {
        "title": "React Admin Dashboard",
        "slug": "react-admin-dashboard",
        "price": Decimal("45.00"),
        "category_slug": "code",
        "subcategory": None,
        "badge": "TOP SOTUV",
        "tech_stack": ["React", "TailwindCSS"],
        "features": [
            "30+ tayyor interaktiv diagrammalar va jadvallar",
            "Foydalanuvchilar va rollar boshqaruvi UI",
            "To'liq moslashuvchan (Responsive) dizayn",
            "Clean TypeScript komponentlari"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80",
        "rating": 4.7,
        "sales_count": 156,
        "telegram_username": "frontpro",
        "description": "Har qanday SaaS, CRM yoki ERP loyihalari uchun mukammal admin paneli shabloni. Qora va oq mavzu, qulay navigatsiya."
    },
    {
        "title": "AI Chat Bot (OpenAI)",
        "slug": "ai-chat-bot",
        "price": Decimal("79.00"),
        "category_slug": "bot",
        "subcategory": None,
        "badge": None,
        "tech_stack": ["Node.js", "Telegram", "AI / OpenAI"],
        "features": [
            "GPT-4o va Claude 3.5 API integratsiyasi",
            "Kontekstni eslab qolish xotira tizimi",
            "Foydalanuvchi limiti va obuna to'lovi boshqaruvi",
            "Ovozli xabarlarni tushunish va Whisper transkripsiya"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=800&q=80",
        "rating": 4.9,
        "sales_count": 98,
        "telegram_username": "ailab",
        "description": "Sun'iy intellekt asosida ishlaydigan universal Telegram chat boti. Har qanday savollarga javob beradi va matn bilan ishlaydi."
    },
    {
        "title": "Landing Page UI Kit",
        "slug": "landing-ui-kit",
        "price": Decimal("19.00"),
        "category_slug": "uikit",
        "subcategory": None,
        "badge": None,
        "tech_stack": ["TailwindCSS", "React"],
        "features": [
            "50+ zamonaviy UI bloklari (Hero, Features, Pricing, FAQ)",
            "Figma manba fayli kiritilgan",
            "Glassmorphism va gradient effektlar",
            "Oson nusxa ko'chirish va moslashtirish"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1545235617-9465d2a55698?w=800&q=80",
        "rating": 4.6,
        "sales_count": 320,
        "telegram_username": "pixelplug",
        "description": "Mahsulotingiz yoki xizmatingiz uchun bir necha daqiqada ajoyib landing sahifa yig'ish imkonini beruvchi dizayn to'plami."
    },
    {
        "title": "Portfolio Sayt Shabloni",
        "slug": "portfolio-template",
        "price": Decimal("25.00"),
        "category_slug": "website",
        "subcategory": "portfolio",
        "badge": None,
        "tech_stack": ["Next.js", "TailwindCSS"],
        "features": [
            "Dasturchi va dizaynerlar uchun shaxsiy brending",
            "Loyihalar va blog bo'limi",
            "Telegram yoki Email orqali aloqa formasi",
            "Lighthouse 100 balli optimallashuv"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80",
        "rating": 4.5,
        "sales_count": 174,
        "telegram_username": "uxmaster",
        "description": "Frilanserlar va dasturchilar uchun o'z tajribasi hamda bajargan ishlarini chiroyli namoyish etuvchi shaxsiy portfolio shabloni."
    },
    {
        "title": "PHP Restoran Boshqaruvi",
        "slug": "php-restaurant",
        "price": Decimal("120.00"),
        "category_slug": "website",
        "subcategory": "restaurant",
        "badge": None,
        "tech_stack": ["PHP", "PostgreSQL"],
        "features": [
            "Stollar band qilish va buyurtmalar navbati",
            "Oshxona ekrani (KDS) moduli",
            "Hisobotlar, daromad va ombor hisobi",
            "Chek chop etish (Thermal printer) drayveri"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800&q=80",
        "rating": 4.4,
        "sales_count": 61,
        "telegram_username": "backendboss",
        "description": "Restoran va kafelarning ichki ish jarayonlarini to'liq avtomatlashtiruvchi professional veb-tizim."
    },
    {
        "title": "Instagram Auto-poster",
        "slug": "instagram-autoposter",
        "price": Decimal("35.00"),
        "category_slug": "code",
        "subcategory": None,
        "badge": None,
        "tech_stack": ["Python"],
        "features": [
            "Rejalashtirilgan post va reels yuklash",
            "Hashtag va tavsiflarni avto-generatsiya",
            "Ko'p akkauntlar bilan ishlash imkoniyati",
            "Xavfsiz proxy qo'llab-quvvatlash"
        ],
        "cover_image_url": "https://images.unsplash.com/photo-1611262588024-d12430b98920?w=800&q=80",
        "rating": 4.3,
        "sales_count": 129,
        "telegram_username": "devbek",
        "description": "SMM mutaxassislari uchun ijtimoiy tarmoqlarga kontentni avtomatik jadval asosida joylovchi Python skripti."
    },
]

class Command(BaseCommand):
    help = "Seeds database with categories, demo users, and products matching wstore Next.js"

    def handle(self, *args, **options):
        self.stdout.write("Boshlang'ich ma'lumotlarni yuklash boshlandi...")

        # 1. Categories
        cat_map = {}
        for c in CATEGORIES_DATA:
            cat_obj, created = Category.objects.update_or_create(
                slug=c["slug"],
                defaults={"name": c["name"], "icon": c["icon"]}
            )
            cat_map[c["slug"]] = cat_obj
            status = "yaratildi" if created else "yangilandi"
            self.stdout.write(f"  Kategoriya: {cat_obj.name} ({status})")

        # 2. Users
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@wstore.uz",
                "first_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            }
        )
        admin_user.set_password("admin123")
        admin_user.save()

        seller_user, _ = User.objects.get_or_create(
            username="seller",
            defaults={
                "email": "seller@wstore.uz",
                "first_name": "wstore demo sotuvchi",
                "role": User.Role.SELLER,
                "balance": 250000,
            }
        )
        seller_user.set_password("seller123")
        seller_user.save()

        buyer_user, _ = User.objects.get_or_create(
            username="buyer",
            defaults={
                "email": "buyer@wstore.uz",
                "first_name": "Demo Xaridor",
                "role": User.Role.BUYER,
                "balance": 100000,
            }
        )
        buyer_user.set_password("buyer123")
        buyer_user.save()

        # 3. Products
        for p in PRODUCTS_DATA:
            cat = cat_map.get(p["category_slug"])
            if not cat:
                continue

            prod, created = Product.objects.update_or_create(
                slug=p["slug"],
                defaults={
                    "title": p["title"],
                    "price": p["price"],
                    "category": cat,
                    "subcategory": p.get("subcategory"),
                    "badge": p.get("badge"),
                    "tech_stack": p["tech_stack"],
                    "features": p.get("features", []),
                    "cover_image_url": p["cover_image_url"],
                    "rating": p["rating"],
                    "sales_count": p["sales_count"],
                    "telegram_username": p.get("telegram_username"),
                    "description": p["description"],
                    "seller": seller_user,
                    "status": Product.Status.ACTIVE,
                }
            )
            status = "yaratildi" if created else "yangilandi"
            self.stdout.write(f"  Mahsulot: {prod.title} ({status})")

        self.stdout.write(self.style.SUCCESS("✅ Seed muvaffaqiyatli yakunlandi!"))
        self.stdout.write(self.style.SUCCESS("Demo akkauntlar:"))
        self.stdout.write("  Admin:   username=admin,   parol=admin123")
        self.stdout.write("  Sotuvchi: username=seller,  parol=seller123")
        self.stdout.write("  Xaridor: username=buyer,   parol=buyer123")

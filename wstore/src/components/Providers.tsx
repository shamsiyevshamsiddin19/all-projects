"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

export type Currency = "USD" | "UZS" | "RUB" | "EUR";
export type Lang = "uz" | "ru" | "en";
export type Theme = "dark" | "light";

// 1 USD -> boshqa valyuta. UZS asosiy bozor valyutasi.
// Kurslarni bitta joyda saqlaymiz — kelajakda admin paneldan yangilash mumkin.
export const RATES: Record<Currency, number> = {
  USD: 1,
  UZS: 12600,
  RUB: 90,
  EUR: 0.92,
};

// Har valyuta uchun ko'rsatiladigan yorliq (belgi/kod). $ ISHLATILMAYDI.
export const CURRENCY_META: Record<
  Currency,
  { code: string; suffix: string; decimals: number }
> = {
  USD: { code: "USD", suffix: "USD", decimals: 0 },
  UZS: { code: "UZS", suffix: "so'm", decimals: 0 },
  RUB: { code: "RUB", suffix: "RUB", decimals: 0 },
  EUR: { code: "EUR", suffix: "EUR", decimals: 0 },
};

export const CURRENCIES: Currency[] = ["USD", "UZS", "RUB", "EUR"];

type AppState = {
  currency: Currency;
  setCurrency: (c: Currency) => void;
  lang: Lang;
  setLang: (l: Lang) => void;
  theme: Theme;
  setTheme: (t: Theme) => void;
};

const AppCtx = createContext<AppState>({
  currency: "USD",
  setCurrency: () => {},
  lang: "uz",
  setLang: () => {},
  theme: "dark",
  setTheme: () => {},
});

export function Providers({
  children,
  initialTheme = "dark",
}: {
  children: ReactNode;
  initialTheme?: Theme;
}) {
  const [currency, setCur] = useState<Currency>("USD");
  const [lang, setLng] = useState<Lang>("uz");
  const [theme, setThm] = useState<Theme>(initialTheme);

  useEffect(() => {
    const c = localStorage.getItem("cur");
    if (c && (CURRENCIES as string[]).includes(c)) setCur(c as Currency);
    const l = localStorage.getItem("lang");
    if (l === "uz" || l === "ru" || l === "en") setLng(l);
  }, []);

  const setCurrency = (c: Currency) => {
    setCur(c);
    localStorage.setItem("cur", c);
  };
  const setLang = (l: Lang) => {
    setLng(l);
    localStorage.setItem("lang", l);
    document.documentElement.lang = l;
  };
  const setTheme = (t: Theme) => {
    setThm(t);
    // Cookie orqali — keyingi sahifa yuklanishida server to'g'ridan HTML'ga
    // yozadi, <a> havolalarda rang muammosi bo'lmasligi uchun.
    document.cookie = `theme=${t}; path=/; max-age=31536000; SameSite=Lax`;
    // Sahifani qayta yuklaymiz — shu bilan barcha elementlar (jumladan
    // ba'zi brauzerlarda CSS o'zgaruvchisini "jonli" yangilamaydigan
    // havolalar) to'g'ri, yangi tema bilan qaytadan chiziladi.
    window.location.reload();
  };

  return (
    <AppCtx.Provider
      value={{ currency, setCurrency, lang, setLang, theme, setTheme }}
    >
      {children}
    </AppCtx.Provider>
  );
}

export const useApp = () => useContext(AppCtx);

// Narxni tanlangan valyutada, belgisiz (kod bilan) formatlaydi. $ yo'q.
export function formatPrice(usd: number, currency: Currency): string {
  const meta = CURRENCY_META[currency];
  const value = usd * RATES[currency];
  const rounded =
    meta.decimals > 0
      ? value.toFixed(meta.decimals)
      : String(Math.round(value));
  // minglikni bo'sh joy bilan ajratamiz: 365 400
  const [intPart, decPart] = rounded.split(".");
  const spaced = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  const num = decPart ? `${spaced}.${decPart}` : spaced;
  return `${num} ${meta.suffix}`;
}

// --- oddiy i18n (barcha asosiy UI matnlari) ---
const DICT = {
  // navigatsiya
  catalog: { uz: "Katalog", ru: "Каталог", en: "Catalog" },
  addProject: {
    uz: "Loyiha qo'shish",
    ru: "Добавить проект",
    en: "Add project",
  },
  cabinet: { uz: "Kabinet", ru: "Кабинет", en: "Cabinet" },
  seller: { uz: "Sotuvchi", ru: "Продавец", en: "Seller" },
  menu: { uz: "Menyu", ru: "Меню", en: "Menu" },
  close: { uz: "Yopish", ru: "Закрыть", en: "Close" },

  // buyurtma / mahsulot
  order: { uz: "Buyurtma", ru: "Заказать", en: "Order" },
  backToCatalog: {
    uz: "Katalogga qaytish",
    ru: "Назад в каталог",
    en: "Back to catalog",
  },
  sales: { uz: "sotuv", ru: "продаж", en: "sales" },
  about: { uz: "Mahsulot haqida", ru: "О товаре", en: "About" },
  features: { uz: "Xususiyatlar", ru: "Характеристики", en: "Features" },
  reviews: { uz: "Izohlar", ru: "Отзывы", en: "Reviews" },
  askSeller: {
    uz: "Sotuvchi bilan bog'lanish",
    ru: "Связаться с продавцом",
    en: "Contact the seller",
  },
  contactShort: { uz: "Bog'lanish", ru: "Связаться", en: "Contact" },
  buyShort: { uz: "To'lov", ru: "Оплата", en: "Pay" },
  showLess: { uz: "Kamroq", ru: "Меньше", en: "Less" },
  topSelling: {
    uz: "Eng ko'p sotilganlar",
    ru: "Хиты продаж",
    en: "Best sellers",
  },
  newArrivals: {
    uz: "Yangi qo'shilganlar",
    ru: "Новые поступления",
    en: "New arrivals",
  },
  loadMore: { uz: "Yana yuklash", ru: "Показать ещё", en: "Load more" },
  searchPlaceholder: {
    uz: "Mahsulot qidirish...",
    ru: "Поиск товара...",
    en: "Search products...",
  },
  buyOnline: {
    uz: "Onlayn to'lov (Click)",
    ru: "Оплатить онлайн (Click)",
    en: "Pay online (Click)",
  },
  processing: { uz: "Yuborilmoqda...", ru: "Отправка...", en: "Processing..." },
  orderPending: {
    uz: "To'lov kutilmoqda",
    ru: "Ожидается оплата",
    en: "Payment pending",
  },
  orderPaid: {
    uz: "To'lov qabul qilindi",
    ru: "Оплата получена",
    en: "Payment received",
  },
  orderFailed: {
    uz: "To'lov amalga oshmadi",
    ru: "Платёж не прошёл",
    en: "Payment failed",
  },
  download: { uz: "Yuklab olish", ru: "Скачать", en: "Download" },
  backToProduct: {
    uz: "Mahsulotga qaytish",
    ru: "Назад к товару",
    en: "Back to product",
  },
  moreProducts: {
    uz: "Boshqa mahsulotlar",
    ru: "Другие товары",
    en: "More products",
  },
  recommended: {
    uz: "Tavsiya etamiz",
    ru: "Рекомендуем",
    en: "Recommended",
  },
  writeReview: {
    uz: "Izoh qoldirish",
    ru: "Оставить отзыв",
    en: "Write a review",
  },
  yourRating: { uz: "Bahoyingiz", ru: "Ваша оценка", en: "Your rating" },
  reviewPlaceholder: {
    uz: "Mahsulot haqida fikringiz...",
    ru: "Ваше мнение о товаре...",
    en: "Your thoughts about the product...",
  },
  send: { uz: "Yuborish", ru: "Отправить", en: "Send" },
  signInToReview: {
    uz: "Izoh qoldirish uchun Google bilan kiring",
    ru: "Войдите через Google, чтобы оставить отзыв",
    en: "Sign in with Google to leave a review",
  },
  noReviews: {
    uz: "Hozircha izoh yo'q. Birinchi bo'ling!",
    ru: "Пока нет отзывов. Будьте первым!",
    en: "No reviews yet. Be the first!",
  },
  reviewSaved: {
    uz: "Izohingiz saqlandi. Rahmat!",
    ru: "Ваш отзыв сохранён. Спасибо!",
    en: "Your review is saved. Thanks!",
  },

  // sayt kichik yo'nalishlari (chiplar)
  subAll: { uz: "Hammasi", ru: "Все", en: "All" },
  subPortfolio: { uz: "Portfolio", ru: "Портфолио", en: "Portfolio" },
  subTeacher: { uz: "O'qituvchilar", ru: "Учителя", en: "Teachers" },
  subEdu: { uz: "O'quv markaz", ru: "Учебный центр", en: "Education" },
  subPharmacy: { uz: "Dorixona", ru: "Аптека", en: "Pharmacy" },
  subRestaurant: { uz: "Restoran", ru: "Ресторан", en: "Restaurant" },
  subOther: { uz: "Boshqa", ru: "Другое", en: "Other" },

  // filtr / saralash
  filter: { uz: "Filtr", ru: "Фильтр", en: "Filter" },
  sort: { uz: "Saralash", ru: "Сортировка", en: "Sort" },
  clear: { uz: "Tozalash", ru: "Очистить", en: "Clear" },
  priceRange: { uz: "Narx oralig'i", ru: "Диапазон цен", en: "Price range" },
  category: { uz: "Kategoriya", ru: "Категория", en: "Category" },
  technology: { uz: "Texnologiya", ru: "Технология", en: "Technology" },
  currency: { uz: "Valyuta", ru: "Валюта", en: "Currency" },

  // saralash variantlari
  sortPopular: { uz: "Ommabop", ru: "Популярные", en: "Popular" },
  sortCheap: {
    uz: "Narx: arzon → qimmat",
    ru: "Цена: дешёвые → дорогие",
    en: "Price: low → high",
  },
  sortExpensive: {
    uz: "Narx: qimmat → arzon",
    ru: "Цена: дорогие → дешёвые",
    en: "Price: high → low",
  },
  sortRating: { uz: "Reyting", ru: "Рейтинг", en: "Rating" },

  // holat matnlari
  available: {
    uz: "ta mahsulot mavjud",
    ru: "товаров доступно",
    en: "items available",
  },
  notFound: {
    uz: "Bu filtrlar bo'yicha mahsulot topilmadi.",
    ru: "По этим фильтрам ничего не найдено.",
    en: "No items match these filters.",
  },
  show: { uz: "Ko'rsatish", ru: "Показать", en: "Show" },
  signIn: {
    uz: "Google bilan kirish",
    ru: "Войти через Google",
    en: "Sign in with Google",
  },
  signInShort: { uz: "Kirish", ru: "Войти", en: "Sign in" },
} satisfies Record<string, Record<Lang, string>>;

export type TKey = keyof typeof DICT;

export function useT() {
  const { lang } = useApp();
  return (key: TKey) => DICT[key]?.[lang] ?? key;
}

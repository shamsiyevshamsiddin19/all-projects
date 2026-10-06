"use strict";
/*
 * showcase.js — data-driven Projects & Certificates, localized (EN/RU/UZ).
 *
 * TO ADD A PROJECT: copy one { ... } block into the PROJECTS array below.
 *   title  – project name: a plain string (kept the same in every language,
 *            e.g. a short brand-like name) OR {en,ru,uz} if it should read
 *            differently per language
 *   desc   – {en,ru,uz} sentence(s) describing the project
 *   tags   – array of short tech labels (kept in Latin in every language —
 *            that's normal convention for technology names)
 *   link   – URL opened by the "Source Code" / "Open Bot" link
 *   icon   – cover icon: subtitle | cap | robot | desktop | api | database | web | mobile | star
 *   accent – hex colour for the cover glow/icon
 *   image  – (optional) path to a real screenshot/logo; overrides the generated cover
 *
 * TO ADD A CERTIFICATE: copy one { ... } block into the CERTIFICATES array.
 *   title  – certificate name (kept as officially issued — usually English —
 *            in every language, same as you'd list a real credential on a CV)
 *   issuer – plain string (org/brand name, same in every language) OR
 *            {en,ru,uz} for a descriptive (non-brand) issuer
 *   date   – e.g. "Feb 2026"
 *   desc   – {en,ru,uz} one-line summary
 *   link   – (optional) URL to the credential
 *   image  – (optional) path to the certificate image
 * Leave CERTIFICATES empty to show "Coming soon" placeholders.
 */

const PROJECTS = [
    {
        title: "Subtitr Bot",
        desc: {
            en: "AI-powered Telegram bot that generates dual-layer subtitles with a floating vocabulary mode. Supports YouTube, tariffs & payments, a background worker queue and a mini-app.",
            ru: "Telegram-бот на основе ИИ, который создаёт двухслойные субтитры с режимом плавающего словаря. Поддерживает YouTube, тарифы и оплату, фоновую очередь задач и мини-приложение.",
            uz: "AI asosidagi Telegram bot bo'lib, suzuvchi lug'at rejimi bilan ikki qatlamli subtitr yaratadi. YouTube, tariflar va to'lovlarni, fon vazifalar navbatini va mini-ilovani qo'llab-quvvatlaydi.",
        },
        tags: ["Python", "aiogram", "PostgreSQL", "AI"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/subtitr-bot",
        image: "assets/images/projects/subtitr-bot.jpg",
        icon: "subtitle",
        accent: "#38bdf8",
    },
    {
        title: {
            en: "Student Services Bot", ru: "Бот студенческих услуг", uz: "Talaba Xizmatlari Bot",
        },
        desc: {
            en: "Telegram bot for students that generates independent-study work with AI, handles payments and integrates with a web bridge. Backend built on Python with a PostgreSQL database.",
            ru: "Telegram-бот для студентов, который с помощью ИИ создаёт самостоятельные работы, обрабатывает платежи и интегрируется с веб-мостом. Backend написан на Python с базой данных PostgreSQL.",
            uz: "Talabalar uchun Telegram bot bo'lib, AI yordamida mustaqil ishlarni yaratadi, to'lovlarni qayta ishlaydi va veb-ko'prik bilan integratsiyalashadi. Backend Python'da, PostgreSQL bazasi bilan qurilgan.",
        },
        tags: ["Python", "FastAPI", "PostgreSQL", "AI"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/mustaqilbot",
        image: "assets/images/projects/mustaqilbot.jpg?v=2",
        icon: "cap",
        accent: "#a78bfa",
    },
    {
        title: { en: "TATU LMS Bots", ru: "Боты TATU LMS", uz: "TATU LMS Botlari" },
        desc: {
            en: "A suite of Telegram bots built around a shared core, integrating with a university LMS to deliver course data and notifications to students.",
            ru: "Набор Telegram-ботов на едином ядре, интегрированных с университетской LMS для доставки данных о курсах и уведомлений студентам.",
            uz: "Umumiy yadro asosida qurilgan Telegram botlar to'plami bo'lib, universitet LMS tizimi bilan integratsiyalashib, talabalarga kurs ma'lumotlari va bildirishnomalarni yetkazadi.",
        },
        tags: ["Python", "Telegram", "LMS"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/tatu-bots",
        image: "assets/images/projects/tatu-bots.jpg",
        icon: "robot",
        accent: "#fbbf24",
    },
    {
        title: "Subtitr Desktop",
        desc: {
            en: "Desktop application that produces dual subtitles offline, paired with a Chrome extension and a packaged Windows installer for one-click setup.",
            ru: "Настольное приложение, создающее двойные субтитры офлайн, в паре с расширением для Chrome и установщиком для Windows для установки в один клик.",
            uz: "Oflayn rejimda ikki qatlamli subtitr yaratadigan desktop ilova, Chrome kengaytmasi va bir marta bosish bilan o'rnatiladigan Windows o'rnatuvchisi bilan birga keladi.",
        },
        tags: ["Python", "FFmpeg", "Desktop", "Chrome Ext"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/subtitr-desktop",
        image: "assets/images/projects/subtitr-desktop.jpg",
        icon: "desktop",
        accent: "#34d399",
    },
    {
        title: "Quiz Bot",
        desc: {
            en: "Telegram quiz bot with a PostgreSQL-backed question bank and an admin panel for managing quizzes, questions and users.",
            ru: "Telegram-бот для викторин с базой вопросов на PostgreSQL и админ-панелью для управления викторинами, вопросами и пользователями.",
            uz: "PostgreSQL asosidagi savollar bazasi va viktorinalar, savollar hamda foydalanuvchilarni boshqarish uchun admin panelli Telegram viktorina boti.",
        },
        tags: ["Python", "aiogram", "PostgreSQL"],
        link: "https://t.me/tez_quizbot",
        linkLabelKey: "open_bot",
        linkIcon: "ri-telegram-line",
        image: "assets/images/projects/quizbot.jpg",
        icon: "web",
        accent: "#f472b6",
    },
    {
        title: "wstore",
        desc: {
            en: "Digital-products marketplace (wstore.uz) for selling code projects, bots and websites. Built with Next.js 15, Prisma and PostgreSQL, with Google auth, Payme/Click payments and admin & seller dashboards.",
            ru: "Маркетплейс цифровых товаров (wstore.uz) для продажи кодовых проектов, ботов и сайтов. Построен на Next.js 15, Prisma и PostgreSQL: вход через Google, оплата Payme/Click, панели администратора и продавца.",
            uz: "Kod loyihalari, botlar va saytlarni sotish uchun raqamli mahsulotlar marketpleysi (wstore.uz). Next.js 15, Prisma va PostgreSQL asosida: Google orqali kirish, Payme/Click to'lovlari, admin va sotuvchi panellari.",
        },
        tags: ["Next.js", "TypeScript", "Prisma", "PostgreSQL"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/wstore",
        image: "assets/images/projects/wstore.jpg?v=2",
        icon: "web",
        accent: "#10b981",
    },
    {
        title: { en: "Document Convertor Bot", ru: "Бот конвертации документов", uz: "Hujjat Konvertor Bot" },
        desc: {
            en: "Telegram bot that converts documents: image/file → PDF/ZIP, Office → PDF, PDF ↔ DOCX, OCR, plus merge, split and watermark. Heavy conversions run off the event loop; the admin panel lives on the web.",
            ru: "Telegram-бот для конвертации документов: изображение/файл → PDF/ZIP, Office → PDF, PDF ↔ DOCX, OCR, а также объединение, разделение и водяной знак. Тяжёлые конвертации вынесены из event-loop; админ-панель — в вебе.",
            uz: "Hujjatlarni konvertatsiya qiluvchi Telegram bot: rasm/fayl → PDF/ZIP, Office → PDF, PDF ↔ DOCX, OCR, hamda birlashtirish, qirqish va watermark. Og'ir konvertatsiyalar event-loop'dan tashqarida; admin panel saytda.",
        },
        tags: ["Python", "aiogram", "PostgreSQL", "OCR"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/document-convertor",
        image: "assets/images/projects/document-convertor.jpg?v=2",
        icon: "api",
        accent: "#f97316",
    },
    {
        title: "Kino Bot",
        desc: {
            en: "Telegram bot for searching and downloading movies and series, with inline search and a web admin panel. Migrated from PHP to Python (aiogram 3) with PostgreSQL.",
            ru: "Telegram-бот для поиска и скачивания фильмов и сериалов с inline-поиском и веб-админкой. Перенесён с PHP на Python (aiogram 3) с PostgreSQL.",
            uz: "Kino va seriallarni qidirish va yuklab olish uchun Telegram bot — inline qidiruv va web-admin panel bilan. PHP'dan Python'ga (aiogram 3) PostgreSQL bilan ko'chirilgan.",
        },
        tags: ["Python", "aiogram", "PostgreSQL"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/kino-bot",
        image: "assets/images/projects/kino-bot.jpg?v=2",
        icon: "robot",
        accent: "#ef4444",
    },
    {
        title: { en: "Session Prep Bot", ru: "Бот подготовки к сессии", uz: "Sessiya Tayyorgarlik Bot" },
        desc: {
            en: "Telegram bot selling exam-session study materials, with Click payments, a referral system and HWID-based activation keys. Python + PostgreSQL, migrated from a PHP bot.",
            ru: "Telegram-бот по продаже материалов для подготовки к сессии: оплата Click, реферальная система и ключи активации на основе HWID. Python + PostgreSQL, перенесён с PHP-бота.",
            uz: "Sessiyaga tayyorgarlik materiallarini sotuvchi Telegram bot — Click to'lovlari, referal tizimi va HWID asosidagi faollashtirish kalitlari bilan. Python + PostgreSQL, PHP botdan ko'chirilgan.",
        },
        tags: ["Python", "aiogram", "PostgreSQL"],
        link: "https://github.com/shamsiyevshamsiddin19/vibe-coding/tree/main/sessiyabot",
        image: "assets/images/projects/sessiyabot.jpg?v=2",
        icon: "database",
        accent: "#06b6d4",
    },
];

const CERTIFICATES = [
    {
        title: "Five Million AI Leaders",
        issuer: { en: "Gov. of Uzbekistan & UAE", ru: "Правительства Узбекистана и ОАЭ", uz: "O'zbekiston va BAA hukumati" },
        date: "Feb 2026",
        desc: {
            en: "Government initiative (Uzbekistan & UAE) training AI leaders in prompt engineering for AI systems.",
            ru: "Государственная инициатива (Узбекистан и ОАЭ) по подготовке лидеров в области ИИ и prompt-инжиниринга для ИИ-систем.",
            uz: "AI tizimlari uchun prompt-injiniring bo'yicha AI yetakchilarini tayyorlaydigan davlat dasturi (O'zbekiston va BAA).",
        },
        link: "",
        image: "assets/images/certificates/five-million-ai-leaders.jpg",
        accent: "#2f6bff",
    },
    {
        title: "Data Analysis with Python",
        issuer: "IBM",
        date: "May 2025",
        desc: {
            en: "Data analysis with Python — Pandas, NumPy, data cleaning and visualization.",
            ru: "Анализ данных на Python — Pandas, NumPy, очистка и визуализация данных.",
            uz: "Python'da ma'lumotlarni tahlil qilish — Pandas, NumPy, ma'lumotlarni tozalash va vizualizatsiya.",
        },
        link: "https://coursera.org/verify/0EGBV79CGC20",
        image: "assets/images/certificates/ibm-data-analysis-python.jpg",
        accent: "#1f70c1",
    },
    {
        title: "Introduction to Large Language Models",
        issuer: "Google Cloud",
        date: "May 2025",
        desc: {
            en: "How large language models work, their use cases and prompt design.",
            ru: "Как работают большие языковые модели, их применение и разработка промптов.",
            uz: "Katta til modellari qanday ishlashi, ularning qo'llanilishi va prompt yaratish.",
        },
        link: "https://coursera.org/verify/64V4YNO2LTJF",
        image: "assets/images/certificates/gcp-large-language-models.jpg",
        accent: "#4285f4",
    },
    {
        title: "Introduction to Generative AI",
        issuer: "Google Cloud",
        date: "May 2025",
        desc: {
            en: "Foundations of generative AI — models, applications and Google Cloud tooling.",
            ru: "Основы генеративного ИИ — модели, применение и инструменты Google Cloud.",
            uz: "Generativ AI asoslari — modellar, qo'llanilishi va Google Cloud vositalari.",
        },
        link: "https://coursera.org/verify/N0A65Q2TO1AX",
        image: "assets/images/certificates/gcp-generative-ai.jpg",
        accent: "#4285f4",
    },
    {
        title: "Responsible AI: Applying AI Principles",
        issuer: "Google Cloud",
        date: "May 2025",
        desc: {
            en: "Applying Google's AI principles to build responsible AI systems.",
            ru: "Применение принципов ИИ от Google для создания ответственных ИИ-систем.",
            uz: "Mas'uliyatli AI tizimlarini yaratish uchun Google AI tamoyillarini qo'llash.",
        },
        link: "https://coursera.org/verify/PIC628894E7X",
        image: "assets/images/certificates/gcp-responsible-ai-applying.jpg",
        accent: "#4285f4",
    },
    {
        title: "Introduction to Responsible AI",
        issuer: "Google Cloud",
        date: "May 2025",
        desc: {
            en: "Foundations of fair, transparent and responsible AI.",
            ru: "Основы справедливого, прозрачного и ответственного ИИ.",
            uz: "Adolatli, shaffof va mas'uliyatli AI asoslari.",
        },
        link: "https://coursera.org/verify/VCFL16J43U4Z",
        image: "assets/images/certificates/gcp-intro-responsible-ai.jpg",
        accent: "#4285f4",
    },
    {
        title: "The Science of Well-Being",
        issuer: "Yale University",
        date: "Feb 2026",
        desc: {
            en: "Science-based habits for well-being, focus and productivity.",
            ru: "Научно обоснованные привычки для благополучия, концентрации и продуктивности.",
            uz: "Farovonlik, diqqat va samaradorlik uchun ilmiy asoslangan odatlar.",
        },
        link: "https://coursera.org/verify/LA35MCYABAF8",
        image: "assets/images/certificates/yale-science-of-well-being.jpg",
        accent: "#5b8def",
    },
    {
        title: "Work Smarter, Not Harder: Time Management",
        issuer: "UC Irvine",
        date: "Feb 2026",
        desc: {
            en: "Time-management and productivity techniques for focused work.",
            ru: "Техники тайм-менеджмента и продуктивности для сфокусированной работы.",
            uz: "Diqqatli ish uchun vaqtni boshqarish va samaradorlik texnikalari.",
        },
        link: "https://coursera.org/verify/51O1ENK8M9YK",
        image: "assets/images/certificates/uci-time-management.jpg",
        accent: "#2563eb",
    },
    {
        title: "Getting Started with Microsoft Excel",
        issuer: "Coursera Project",
        date: "Feb 2026",
        desc: {
            en: "Spreadsheet fundamentals — formulas, formatting and data basics.",
            ru: "Основы электронных таблиц — формулы, форматирование и работа с данными.",
            uz: "Elektron jadvallar asoslari — formulalar, formatlash va ma'lumotlar bilan ishlash.",
        },
        link: "https://coursera.org/verify/3A1G0HAN5Q5M",
        image: "assets/images/certificates/excel-getting-started.jpg",
        accent: "#21a366",
    },
    {
        title: "Build Your Business Brand Using Canva",
        issuer: "Coursera Project",
        date: "Feb 2026",
        desc: {
            en: "Building a business brand and visual identity with Canva.",
            ru: "Создание бренда бизнеса и визуального стиля с помощью Canva.",
            uz: "Canva yordamida biznes brendi va vizual uslubni yaratish.",
        },
        link: "https://coursera.org/verify/I9Y6YOZMRQFY",
        image: "assets/images/certificates/canva-business-brand.jpg",
        accent: "#7d2ae8",
    },
    {
        title: "IQ Test Certificate (Score 118)",
        issuer: "myIQ",
        date: "May 2025",
        desc: {
            en: "Standardized cognitive assessment — measured IQ score of 118.",
            ru: "Стандартизированная когнитивная оценка — измеренный IQ составил 118.",
            uz: "Standartlashtirilgan kognitiv baholash — o'lchangan IQ ko'rsatkichi 118.",
        },
        link: "",
        image: "assets/images/certificates/myiq-iq-test.jpg",
        accent: "#2563eb",
    },
];

// How many placeholder cards to show while CERTIFICATES is empty.
const CERT_PLACEHOLDERS = 3;

// UI strings used by the generated cards (project/certificate content itself
// is localized via the {en,ru,uz} fields above).
const UI = {
    en: { source_code: "Source Code", open_bot: "Open Bot", view_credential: "View credential", view_certificate: "View certificate", coming_soon: "Coming soon", cert_title: "Certificate", cert_desc: "Professional certificates and achievements will appear here soon.", project_label: "Project", certificate_label: "Certificate" },
    ru: { source_code: "Исходный код", open_bot: "Открыть бота", view_credential: "Посмотреть сертификат", view_certificate: "Посмотреть сертификат", coming_soon: "Скоро", cert_title: "Сертификат", cert_desc: "Профессиональные сертификаты и достижения скоро появятся здесь.", project_label: "Проект", certificate_label: "Сертификат" },
    uz: { source_code: "Manba kodi", open_bot: "Botni ochish", view_credential: "Sertifikatni ko'rish", view_certificate: "Sertifikatni ko'rish", coming_soon: "Tez orada", cert_title: "Sertifikat", cert_desc: "Professional sertifikatlar va yutuqlar tez orada shu yerda paydo bo'ladi.", project_label: "Loyiha", certificate_label: "Sertifikat" },
};

function currentLang() {
    const saved = localStorage.getItem("siteLang");
    return (saved === "ru" || saved === "uz") ? saved : "en";
}

// A field is either a plain string (identical in every language — brand
// names, technology names) or an {en,ru,uz} object.
function pick(field, lang) {
    if (field == null) return "";
    if (typeof field === "string") return field;
    return field[lang] || field.en || "";
}

// --- helpers -------------------------------------------------------------
function esc(str) {
    return String(str == null ? "" : str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

// Cover icons — drawn centred on (0,0), stroked in the accent colour.
const ICONS = {
    subtitle: () => `<rect x="-52" y="-34" width="104" height="68" rx="12"/><path d="M-34 -8 H-12"/><path d="M-2 -8 H34"/><path d="M-34 8 H-4"/><path d="M6 8 H34"/>`,
    cap: (a) => `<path d="M0 -30 L52 -6 L0 18 L-52 -6 Z"/><path d="M-26 2 V22 C-26 22 0 35 26 22 V2"/><path d="M52 -6 V20"/><circle cx="52" cy="24" r="4" fill="${a}" stroke="none"/>`,
    robot: (a) => `<rect x="-40" y="-25" width="80" height="60" rx="14"/><path d="M0 -25 V-39"/><path d="M-16 21 H16"/><path d="M-40 -1 H-50"/><path d="M40 -1 H50"/><circle cx="0" cy="-43" r="4" fill="${a}" stroke="none"/><circle cx="-17" cy="1" r="4.5" fill="${a}" stroke="none"/><circle cx="17" cy="1" r="4.5" fill="${a}" stroke="none"/>`,
    desktop: (a) => `<rect x="-54" y="-36" width="108" height="68" rx="8"/><path d="M-10 32 V44"/><path d="M10 32 V44"/><path d="M-24 46 H24"/><path d="M-34 16 H10"/><path d="M-12 -14 V6 L6 -4 Z" fill="${a}" stroke="none"/>`,
    api: () => `<path d="M-16 -18 L-38 4 L-16 26"/><path d="M16 -18 L38 4 L16 26"/><path d="M6 -22 L-6 28"/>`,
    database: () => `<path d="M-34 -22 C-34 -29 34 -29 34 -22"/><path d="M-34 -22 V22 C-34 29 34 29 34 22 V-22"/><path d="M-34 0 C-34 7 34 7 34 0"/>`,
    web: () => `<circle cx="0" cy="0" r="38"/><path d="M-38 0 H38"/><path d="M0 -38 V38"/><path d="M-30 -20 C-14 -10 14 -10 30 -20"/><path d="M-30 20 C-14 10 14 10 30 20"/><path d="M0 -38 C-20 -20 -20 20 0 38"/><path d="M0 -38 C20 -20 20 20 0 38"/>`,
    mobile: () => `<rect x="-24" y="-40" width="48" height="80" rx="8"/><path d="M-8 -30 H8"/><path d="M-6 28 H6"/>`,
    star: () => `<path d="M0 -34 L10 -10 L36 -8 L16 8 L22 34 L0 20 L-22 34 L-16 8 L-36 -8 L-10 -10 Z"/>`,
};

function coverSVG(title, p, i) {
    const accent = p.accent || "#38bdf8";
    const label = esc((p.category || (p.tags || []).slice(0, 3).join(" · ")).toUpperCase());
    const draw = (ICONS[p.icon] || ICONS.star)(accent);
    return `<svg class="cover-svg" viewBox="0 0 400 250" preserveAspectRatio="xMidYMid slice" role="img" aria-label="${esc(title)}">
        <defs>
            <radialGradient id="cg${i}" cx="78%" cy="18%" r="75%">
                <stop offset="0%" stop-color="${accent}" stop-opacity="0.30"/>
                <stop offset="55%" stop-color="${accent}" stop-opacity="0.05"/>
                <stop offset="100%" stop-color="${accent}" stop-opacity="0"/>
            </radialGradient>
            <pattern id="cp${i}" width="26" height="26" patternUnits="userSpaceOnUse">
                <path d="M26 0H0V26" fill="none" stroke="#ffffff" stroke-opacity="0.04" stroke-width="1"/>
            </pattern>
        </defs>
        <rect width="400" height="250" fill="#0d0d0d"/>
        <rect width="400" height="250" fill="url(#cp${i})"/>
        <rect width="400" height="250" fill="url(#cg${i})"/>
        <g transform="translate(200,102)" fill="none" stroke="${accent}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">${draw}</g>
        <text x="200" y="205" text-anchor="middle" font-family="'Outfit',Arial,sans-serif" font-size="12" font-weight="500" fill="#8a8a8a" letter-spacing="3">${label}</text>
    </svg>`;
}

function stackCard(p, i, total, lang) {
    const t = UI[lang];
    const title = pick(p.title, lang);
    const desc = pick(p.desc, lang);
    const cover = p.image
        ? `<img src="${esc(p.image)}" alt="${esc(title)}" loading="eager" decoding="async">`
        : coverSVG(title, p, i);
    const tags = (p.tags || []).map((tg) => `<span class="tag">${esc(tg)}</span>`).join("");
    const num = String(i + 1).padStart(2, "0");
    const tot = String(total).padStart(2, "0");
    const accent = p.accent || "#38bdf8";
    const linkIcon = p.linkIcon || "ri-github-line";
    const linkLabel = p.linkLabelKey ? t[p.linkLabelKey] : t.source_code;
    return `<article class="pcard" style="--accent:${esc(accent)}">
        <div class="pcard-cover">${cover}</div>
        <div class="pcard-body">
            <div class="pcard-index">${num} / ${tot}</div>
            <h3>${esc(title)}</h3>
            <p>${esc(desc)}</p>
            <div class="tags">${tags}</div>
            <a href="${esc(p.link)}" target="_blank" rel="noopener" class="project-link"><i class="${esc(linkIcon)}" aria-hidden="true"></i> ${esc(linkLabel)}</a>
        </div>
    </article>`;
}

// Strip any previously-bound listeners from a persistent element (arrow
// buttons survive across re-renders when the language changes) by cloning
// it and swapping it in — clones carry no JS listeners.
function fresh(el) {
    if (!el) return el;
    const clone = el.cloneNode(true);
    el.parentNode.replaceChild(clone, el);
    return clone;
}

// Wire a two-sided "fan" deck: the front card sits centred & upright, the rest
// fan out symmetrically to the left and right. Arrows, dots, clicking a side
// card and swipe all cycle which card is in front. Reused by projects & certs.
// Safe to call again (e.g. after a language switch re-renders the cards).
function initFanDeck(deckId, stageId, dotsId, label) {
    const deck = document.getElementById(deckId);
    const stage = document.getElementById(stageId);
    const dotsWrap = document.getElementById(dotsId);
    if (!deck || !stage) return;
    const cards = Array.from(stage.children);
    const n = cards.length;
    if (!n) return;

    let front = 0;

    if (dotsWrap) {
        dotsWrap.innerHTML = cards
            .map((_, i) => `<button class="spot-dot${i === 0 ? " active" : ""}" type="button" aria-label="${esc(label || "Item")} ${i + 1}"></button>`)
            .join("");
    }
    const dots = dotsWrap ? Array.from(dotsWrap.children) : [];

    const render = () => {
        cards.forEach((card, i) => {
            const r = (i - front + n) % n;                 // 0 = front card
            const k = Math.min(r, n - r);                  // depth into the stack
            // side: +1 spreads right, -1 spreads left, 0 stays on the vertical axis.
            // The card exactly opposite the front (r === n - r) sits on the axis,
            // so the layout is always mirror-symmetric about the vertical centre.
            const side = (r === 0 || r === n - r) ? 0 : (r < n - r ? 1 : -1);
            const x = side * k;                            // signed horizontal units
            const y = side === 0 ? -k : k;                 // axis cards peek up; side cards drop down
            // Cards stay upright — no rotation.
            card.style.transform =
                `translateX(calc(var(--fan-x) * ${x})) ` +
                `translateY(calc(var(--fan-y) * ${y})) ` +
                `scale(${(1 - k * 0.055).toFixed(3)})`;
            card.style.zIndex = String(100 - k);
            // Only the front card is crisp. Cards behind it recede into a soft,
            // dimmed, blurred backdrop so their text never competes with the front.
            if (k === 0) {
                card.style.opacity = "1";
                card.style.filter = "none";
                card.style.pointerEvents = "auto";
            } else {
                card.style.opacity = String(Math.max(0.18, 0.5 - (k - 1) * 0.17));
                card.style.filter = `blur(${2 + k * 2.5}px) brightness(${(1 - k * 0.14).toFixed(2)})`;
            }
            card.dataset.front = r === 0 ? "1" : "0";
            card.setAttribute("aria-hidden", r === 0 ? "false" : "true");
        });
        dots.forEach((dot, i) => dot.classList.toggle("active", i === front));
    };
    const go = (step) => { front = (front + step + n) % n; render(); };

    // Arrow buttons persist across re-renders (they live outside the stage
    // that gets its innerHTML replaced), so clone-replace them first to
    // guarantee we never stack up duplicate click listeners.
    const prev = fresh(deck.querySelector(".pdeck-arrow.prev"));
    const next = fresh(deck.querySelector(".pdeck-arrow.next"));
    if (prev) prev.addEventListener("click", () => go(-1));
    if (next) next.addEventListener("click", () => go(1));
    dots.forEach((dot, i) => dot.addEventListener("click", () => { front = i; render(); }));

    // Click behaviour: a card behind the front comes forward; clicking the front
    // card advances to the next one — but a tap on the Source Code link still
    // opens it normally.
    cards.forEach((card, i) => {
        card.addEventListener("click", (e) => {
            if (card.dataset.front === "1") {
                if (e.target.closest("a")) return;
                e.preventDefault();
                go(1);
            } else {
                e.preventDefault();
                front = i;
                render();
            }
        });
    });

    // Touch swipe on the stage. The stage element itself persists across
    // re-renders (only its children are replaced), so guard with a flag to
    // avoid binding this listener more than once.
    if (!stage.dataset.swipeBound) {
        stage.dataset.swipeBound = "1";
        let sx = null;
        stage.addEventListener("touchstart", (e) => { sx = e.changedTouches[0].screenX; }, { passive: true });
        stage.addEventListener("touchend", (e) => {
            if (sx == null) return;
            const dx = e.changedTouches[0].screenX - sx;
            if (Math.abs(dx) > 45) go(dx < 0 ? 1 : -1);
            sx = null;
        }, { passive: true });
    }

    // Only one card: nothing to navigate
    const controls = deck.querySelector(".pdeck-controls");
    if (controls) controls.style.display = n < 2 ? "none" : "";

    render();
}

function certFanCard(c, i, total, lang) {
    const t = UI[lang];
    const accent = (c && c.accent) || "#fbbf24";
    const num = String(i + 1).padStart(2, "0");
    const tot = String(total).padStart(2, "0");
    if (!c) {
        const cover = coverSVG(t.cert_title, { icon: "star", accent, tags: [t.coming_soon] }, "c" + i);
        return `<article class="pcard" style="--accent:${accent}" aria-disabled="true">
            <div class="pcard-cover">${cover}</div>
            <div class="pcard-body">
                <div class="pcard-index">${num} / ${tot}</div>
                <h3>${esc(t.cert_title)}</h3>
                <p>${esc(t.cert_desc)}</p>
                <span class="project-link" style="opacity:.65"><i class="ri-time-line" aria-hidden="true"></i> ${esc(t.coming_soon)}</span>
            </div>
        </article>`;
    }
    const title = pick(c.title, lang);
    const issuer = pick(c.issuer, lang);
    const desc = pick(c.desc, lang);
    const cover = c.image
        ? `<img src="${esc(c.image)}" alt="${esc(title)}" loading="${i === 0 ? "eager" : "lazy"}" decoding="async" style="object-position:top;background:#fff">`
        : coverSVG(title, { icon: c.icon || "star", accent, category: issuer }, "c" + i);
    const cta = c.link
        ? `<a class="project-link" href="${esc(c.link)}" target="_blank" rel="noopener"><i class="ri-external-link-line" aria-hidden="true"></i> ${esc(t.view_credential)}</a>`
        : c.image
        ? `<a class="project-link" href="${esc(c.image)}" target="_blank" rel="noopener"><i class="ri-image-line" aria-hidden="true"></i> ${esc(t.view_certificate)}</a>`
        : `<span class="project-link">${esc(issuer)}</span>`;
    return `<article class="pcard" style="--accent:${accent}">
        <div class="pcard-cover">${cover}</div>
        <div class="pcard-body">
            <div class="pcard-index">${esc(c.date || "")}${issuer ? " · " + esc(issuer) : ""}</div>
            <h3>${esc(title)}</h3>
            <p>${esc(desc)}</p>
            ${cta}
        </div>
    </article>`;
}

// --- render ----------------------------------------------------------------
// Exposed globally so i18n.js can call it again whenever the language
// switches (cards are generated from data, not static [data-i18n] text).
function renderShowcase(lang) {
    lang = lang || currentLang();
    const t = UI[lang];
    const projectStage = document.getElementById("projectGrid");
    if (projectStage) {
        projectStage.innerHTML = PROJECTS.map((p, i) => stackCard(p, i, PROJECTS.length, lang)).join("");
        initFanDeck("projectDeck", "projectGrid", "projectDots", t.project_label);
    }
    const certStage = document.getElementById("certGrid");
    if (certStage) {
        const total = CERTIFICATES.length || CERT_PLACEHOLDERS;
        const items = CERTIFICATES.length
            ? CERTIFICATES.map((c, i) => certFanCard(c, i, total, lang))
            : Array.from({ length: CERT_PLACEHOLDERS }, (_, i) => certFanCard(null, i, total, lang));
        certStage.innerHTML = items.join("");
        initFanDeck("certDeck", "certGrid", "certDots", t.certificate_label);
    }
}
window.renderShowcase = renderShowcase;

renderShowcase(currentLang());

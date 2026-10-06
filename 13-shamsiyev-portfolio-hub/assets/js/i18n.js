"use strict";
/*
 * i18n.js — homepage language switcher (EN / RU / UZ).
 * Elements with data-i18n="key" get their text swapped; data-i18n-ph="key"
 * swaps an input/textarea placeholder. Person names are transliterated to
 * Cyrillic for RU (that's the only sane way to "translate" a name); brand
 * and technology names (Python, GitHub, Vue.js...) stay in Latin in every
 * language, matching normal convention. Choice is remembered in localStorage.
 */
const I18N = {
    en: {
        nav_about: "ABOUT", nav_skills: "SKILLS", nav_projects: "PROJECTS",
        nav_certs: "CERTIFICATES", nav_contact: "CONTACT",
        hero_iam: "I AM",
        hero_name: "SHAMSIDDIN",
        btn_view_cv: "VIEW CV", btn_view_resume: "VIEW RESUME",
        scroll_hint: "SCROLL",
        about_h: "ABOUT ME",
        about_p1: "Hi, I'm Shamsiddin — a backend developer from Tashkent. I got into programming in August 2024 and have been hooked ever since, learning the craft under the mentorship of Nurulloh Muhammadov. Most of what I build lives on the server side: Telegram bots, APIs, and the databases and Linux servers behind them.",
        about_p2: "I like shipping things people actually use — like Subtitr Bot, my AI subtitle bot — and I lean on my background in higher mathematics to reason through algorithms. I read English and Russian documentation comfortably, so I rarely stay stuck for long.",
        stat_years: "Years Coding", stat_projects: "Projects", stat_langs: "Languages",
        skills_h: "MY SKILLS",
        skill_database: "Database", skill_webdev: "Web Dev", skill_tools: "Tools & Services", skill_git: "Git & GitHub",
        projects_h: "FEATURED PROJECTS", projects_sub: "SOME OF MY RECENT BACKEND WORK",
        mentors_h: "MENTORS & FRIENDS", mentors_sub: "PEOPLE WHO INSPIRE ME",
        role_backend_mentor: "Backend Mentor", role_frontend_mentor: "Frontend Mentor",
        friends_h: "MY FRIENDS", friends_sub: "AWESOME PEOPLE I KNOW",
        name_shamsiddin: "Shamsiddin Shamsiyev", name_nurulloh: "Nurulloh Muhammadov", name_daler: "Daler Badiyev",
        name_torvalds: "Linus Torvalds", name_vanrossum: "Guido van Rossum", name_abramov: "Dan Abramov",
        name_you: "Evan You", name_dahl: "Ryan Dahl", name_sorhus: "Sindre Sorhus", name_tj: "TJ Holowaychuk",
        name_osmani: "Addy Osmani", name_dodds: "Kent C. Dodds", name_prestonwerner: "Tom Preston-Werner",
        role_linux_git: "Linux & Git", role_nodejs_deno: "Node.js & Deno", role_opensource: "Open Source",
        role_react_testing: "React / Testing", role_github_founder: "GitHub founder",
        certs_h: "CERTIFICATES", certs_sub: "LICENSES & ACHIEVEMENTS",
        contact_h: "CONTACT",
        contact_p: "If you're looking for a dedicated Backend Developer to build scalable systems, or you just have a question, feel free to drop a message. Let's build something great together.",
        cform_h: "CONTACT FORM",
        ph_name: "Name Surname", ph_phone: "Your phone", ph_email: "Your e-mail", ph_msg: "Message",
        btn_send: "SEND MESSAGE",
        lbl_addr: "Address", val_addr: "Tashkent, Uzbekistan", lbl_email: "E-mail",
        f_role: "Backend Developer — Python · Django · FastAPI",
        f_explore: "Explore", f_connect: "Connect", f_backtop: "Back to top",
        f_rights: "All rights reserved.",
    },
    ru: {
        nav_about: "ОБО МНЕ", nav_skills: "НАВЫКИ", nav_projects: "ПРОЕКТЫ",
        nav_certs: "СЕРТИФИКАТЫ", nav_contact: "КОНТАКТ",
        hero_iam: "Я",
        hero_name: "ШАМСИДДИН",
        btn_view_cv: "СМОТРЕТЬ CV", btn_view_resume: "СМОТРЕТЬ РЕЗЮМЕ",
        scroll_hint: "СКРОЛЛ",
        about_h: "ОБО МНЕ",
        about_p1: "Привет, я Шамсиддин — backend-разработчик из Ташкента. Я начал программировать в августе 2024 года и с тех пор не могу остановиться; учусь ремеслу под наставничеством Нуруллоха Мухаммадова. Большая часть моей работы — серверная сторона: Telegram-боты, API, базы данных и Linux-серверы, которые всё это держат.",
        about_p2: "Мне нравится делать вещи, которыми реально пользуются — например, Subtitr Bot, мой бот для субтитров с ИИ — и я опираюсь на базу по высшей математике, чтобы разбираться в алгоритмах. Свободно читаю документацию на английском и русском, поэтому надолго редко застреваю.",
        stat_years: "Года в коде", stat_projects: "Проектов", stat_langs: "Языка",
        skills_h: "МОИ НАВЫКИ",
        skill_database: "База данных", skill_webdev: "Веб-разработка", skill_tools: "Инструменты и сервисы", skill_git: "Git и GitHub",
        projects_h: "ИЗБРАННЫЕ ПРОЕКТЫ", projects_sub: "НЕКОТОРЫЕ ИЗ МОИХ BACKEND-РАБОТ",
        mentors_h: "НАСТАВНИКИ И ДРУЗЬЯ", mentors_sub: "ЛЮДИ, КОТОРЫЕ МЕНЯ ВДОХНОВЛЯЮТ",
        role_backend_mentor: "Backend-наставник", role_frontend_mentor: "Frontend-наставник",
        friends_h: "МОИ ДРУЗЬЯ", friends_sub: "КЛАССНЫЕ ЛЮДИ, КОТОРЫХ Я ЗНАЮ",
        name_shamsiddin: "Шамсиддин Шамсиев", name_nurulloh: "Нурулло Мухаммадов", name_daler: "Далер Бадиев",
        name_torvalds: "Линус Торвальдс", name_vanrossum: "Гвидо ван Россум", name_abramov: "Дэн Абрамов",
        name_you: "Эван Ю", name_dahl: "Райан Даль", name_sorhus: "Синдре Сорхус", name_tj: "Ти Джей Холовайчук",
        name_osmani: "Адди Османи", name_dodds: "Кент Си Доддс", name_prestonwerner: "Том Престон-Вернер",
        role_linux_git: "Linux и Git", role_nodejs_deno: "Node.js и Deno", role_opensource: "Открытый код",
        role_react_testing: "React / Тестирование", role_github_founder: "Основатель GitHub",
        certs_h: "СЕРТИФИКАТЫ", certs_sub: "ЛИЦЕНЗИИ И ДОСТИЖЕНИЯ",
        contact_h: "КОНТАКТ",
        contact_p: "Если вам нужен увлечённый Backend-разработчик для масштабируемых систем или просто есть вопрос — пишите. Давайте создадим что-то классное вместе.",
        cform_h: "ФОРМА СВЯЗИ",
        ph_name: "Имя Фамилия", ph_phone: "Ваш телефон", ph_email: "Ваш e-mail", ph_msg: "Сообщение",
        btn_send: "ОТПРАВИТЬ",
        lbl_addr: "Адрес", val_addr: "Ташкент, Узбекистан", lbl_email: "E-mail",
        f_role: "Backend-разработчик — Python · Django · FastAPI",
        f_explore: "Разделы", f_connect: "Связаться", f_backtop: "Наверх",
        f_rights: "Все права защищены.",
    },
    uz: {
        nav_about: "MEN HAQIMDA", nav_skills: "KO‘NIKMALAR", nav_projects: "LOYIHALAR",
        nav_certs: "SERTIFIKATLAR", nav_contact: "ALOQA",
        hero_iam: "MEN",
        hero_name: "SHAMSIDDIN",
        btn_view_cv: "CV KO‘RISH", btn_view_resume: "REZYUME KO‘RISH",
        scroll_hint: "SKROLL",
        about_h: "MEN HAQIMDA",
        about_p1: "Salom, men Shamsiddinman — Toshkentlik backend dasturchi. Dasturlashni 2024-yil avgustda boshlaganman va o‘shandan beri qiziqishim so‘nmagan; hunarni Nurulloh Muhammadov rahbarligida o‘rganib kelaman. Ishimning ko‘p qismi server tomonida: Telegram botlar, API’lar, hamda ularni ishlatib turadigan ma’lumotlar bazasi va Linux serverlar.",
        about_p2: "Odamlar haqiqatan foydalanadigan narsalar yaratishni yaxshi ko‘raman — masalan, Subtitr Bot (AI subtitr boti) — va algoritmlarni tushunishда oliy matematika bilimimga tayanaman. Ingliz va rus tilidagi hujjatlarni bemalol o‘qiganim uchun uzoq qotib qolmayman.",
        stat_years: "Yil kodlash", stat_projects: "Loyiha", stat_langs: "Til",
        skills_h: "KO‘NIKMALARIM",
        skill_database: "Ma'lumotlar bazasi", skill_webdev: "Veb dasturlash", skill_tools: "Vositalar va xizmatlar", skill_git: "Git va GitHub",
        projects_h: "TANLANGAN LOYIHALAR", projects_sub: "SO‘NGGI BACKEND ISHLARIMDAN",
        mentors_h: "MENTORLAR VA DO‘STLAR", mentors_sub: "MENGA ILHOM BERUVCHI ODAMLAR",
        role_backend_mentor: "Backend mentor", role_frontend_mentor: "Frontend mentor",
        friends_h: "MENING DO‘STLARIM", friends_sub: "BILGAN AJOYIB ODAMLARIM",
        name_shamsiddin: "Shamsiddin Shamsiyev", name_nurulloh: "Nurulloh Muhammadov", name_daler: "Daler Badiyev",
        name_torvalds: "Linus Torvalds", name_vanrossum: "Guido van Rossum", name_abramov: "Dan Abramov",
        name_you: "Evan You", name_dahl: "Ryan Dahl", name_sorhus: "Sindre Sorhus", name_tj: "TJ Holowaychuk",
        name_osmani: "Addy Osmani", name_dodds: "Kent C. Dodds", name_prestonwerner: "Tom Preston-Werner",
        role_linux_git: "Linux va Git", role_nodejs_deno: "Node.js va Deno", role_opensource: "Ochiq manba",
        role_react_testing: "React / Testlash", role_github_founder: "GitHub asoschisi",
        certs_h: "SERTIFIKATLAR", certs_sub: "LITSENZIYA VA YUTUQLAR",
        contact_h: "ALOQA",
        contact_p: "Agar sizga kengaytiriladigan tizimlar quradigan backend dasturchi kerak bo‘lsa yoki shunchaki savolingiz bo‘lsa — yozing. Keling, birga zo‘r narsa yarataylik.",
        cform_h: "ALOQA FORMASI",
        ph_name: "Ism Familiya", ph_phone: "Telefoningiz", ph_email: "E-pochtangiz", ph_msg: "Xabar",
        btn_send: "YUBORISH",
        lbl_addr: "Manzil", val_addr: "Toshkent, O‘zbekiston", lbl_email: "E-pochta",
        f_role: "Backend Dasturchi — Python · Django · FastAPI",
        f_explore: "Bo‘limlar", f_connect: "Bog‘lanish", f_backtop: "Yuqoriga",
        f_rights: "Barcha huquqlar himoyalangan.",
    },
};

(function () {
    const supported = ["en", "ru", "uz"];
    const saved = localStorage.getItem("siteLang");
    const initial = supported.includes(saved) ? saved : "en";

    function apply(lang) {
        const dict = I18N[lang] || I18N.en;
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const v = dict[el.getAttribute("data-i18n")];
            if (v != null) el.textContent = v;
        });
        document.querySelectorAll("[data-i18n-ph]").forEach((el) => {
            const v = dict[el.getAttribute("data-i18n-ph")];
            if (v != null) el.setAttribute("placeholder", v);
        });
        document.documentElement.setAttribute("lang", lang);
        document.querySelectorAll(".site-lang-btn").forEach((b) =>
            b.classList.toggle("active", b.getAttribute("data-lang") === lang)
        );
        localStorage.setItem("siteLang", lang);
        // Project/certificate cards are rendered by showcase.js from data
        // objects, not static [data-i18n] text, so re-render them too.
        if (typeof window.renderShowcase === "function") window.renderShowcase(lang);
        // The hero name can render wider in another script (e.g. Cyrillic
        // capitals) at the same font-size, so re-fit it to the container.
        if (typeof window.fitHeroTitle === "function") window.fitHeroTitle();
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll(".site-lang-btn").forEach((b) =>
            b.addEventListener("click", () => apply(b.getAttribute("data-lang")))
        );
        apply(initial);
    });
})();

-- Yordamchi PostgreSQL sxemasi.
-- Ilova ishga tushganda db.init_schema bu faylni bir marta bajaradi.
-- MUHIM: init_schema faylni nuqta-vergul bo'yicha ajratadi, shuning uchun gap ichida
-- (izohlarda ham) nuqta-vergul ishlatilmaydi.

CREATE TABLE IF NOT EXISTS doktorlar (
    id BIGSERIAL PRIMARY KEY,
    ism VARCHAR(191) NOT NULL,
    email VARCHAR(191) NOT NULL,
    parol_hash VARCHAR(255) DEFAULT NULL,
    firebase_uid VARCHAR(191) DEFAULT NULL,
    kirish_turi VARCHAR(32) NOT NULL DEFAULT 'oddiy',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_doktorlar_email UNIQUE (email),
    CONSTRAINT uq_doktorlar_firebase_uid UNIQUE (firebase_uid)
);

CREATE TABLE IF NOT EXISTS app_storage (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    storage_key VARCHAR(191) NOT NULL,
    storage_value TEXT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_app_storage_owner_key UNIQUE (owner_type, owner_key, storage_key)
);

CREATE INDEX IF NOT EXISTS idx_app_storage_lookup ON app_storage (owner_type, owner_key);

CREATE TABLE IF NOT EXISTS reja_files (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    access_token CHAR(64) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(191) NOT NULL DEFAULT 'application/octet-stream',
    file_ext VARCHAR(32) NOT NULL DEFAULT '',
    file_size BIGINT NOT NULL DEFAULT 0,
    file_data BYTEA NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_reja_files_token UNIQUE (access_token)
);

CREATE INDEX IF NOT EXISTS idx_reja_files_owner ON reja_files (owner_type, owner_key, id);

CREATE TABLE IF NOT EXISTS sport_sync_meta (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    meta_key VARCHAR(64) NOT NULL,
    meta_value VARCHAR(64) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_sport_sync_meta_owner_key UNIQUE (owner_type, owner_key, meta_key)
);

CREATE TABLE IF NOT EXISTS sport_exercises (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    category VARCHAR(64) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    weight DECIMAL(10,2) NOT NULL DEFAULT 0,
    increase_amount DECIMAL(10,2) NOT NULL DEFAULT 0,
    set_count INT NOT NULL DEFAULT 0,
    rep_count INT NOT NULL DEFAULT 0,
    is_deleted SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sport_exercises_owner_category ON sport_exercises (owner_type, owner_key, category, is_deleted);

CREATE INDEX IF NOT EXISTS idx_sport_exercises_updated ON sport_exercises (updated_at);

CREATE TABLE IF NOT EXISTS sport_media (
    id BIGSERIAL PRIMARY KEY,
    exercise_id BIGINT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(32) NOT NULL DEFAULT 'image',
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sport_media_exercise
        FOREIGN KEY (exercise_id) REFERENCES sport_exercises(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sport_media_exercise ON sport_media (exercise_id, sort_order);

CREATE TABLE IF NOT EXISTS quiz_bases (
    id BIGSERIAL PRIMARY KEY,
    full_name VARCHAR(191) NOT NULL,
    subject_name VARCHAR(191) NOT NULL,
    base_name VARCHAR(191) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_quiz_bases_full_name UNIQUE (full_name)
);

CREATE INDEX IF NOT EXISTS idx_quiz_bases_subject ON quiz_bases (subject_name);

CREATE TABLE IF NOT EXISTS quiz_questions (
    id BIGSERIAL PRIMARY KEY,
    base_id BIGINT NOT NULL,
    question_text TEXT NOT NULL,
    options_json TEXT NOT NULL,
    correct_answer VARCHAR(16) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_quiz_questions_base
        FOREIGN KEY (base_id) REFERENCES quiz_bases(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quiz_questions_base_sort ON quiz_questions (base_id, sort_order);

CREATE TABLE IF NOT EXISTS quiz_progress (
    id BIGSERIAL PRIMARY KEY,
    base_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    is_solved SMALLINT NOT NULL DEFAULT 0,
    flag_type VARCHAR(32) NOT NULL DEFAULT '',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_quiz_progress_owner_question UNIQUE (base_id, question_id, owner_type, owner_key),
    CONSTRAINT fk_quiz_progress_base
        FOREIGN KEY (base_id) REFERENCES quiz_bases(id) ON DELETE CASCADE,
    CONSTRAINT fk_quiz_progress_question
        FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_quiz_progress_owner ON quiz_progress (owner_type, owner_key);

CREATE TABLE IF NOT EXISTS goal_folders (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    name VARCHAR(191) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goal_folders_owner ON goal_folders (owner_type, owner_key, sort_order);

CREATE TABLE IF NOT EXISTS goal_sections (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    folder_id BIGINT NULL,
    name VARCHAR(191) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goal_sections_owner_folder ON goal_sections (owner_type, owner_key, folder_id, sort_order);

CREATE TABLE IF NOT EXISTS goals (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    folder_id BIGINT NULL,
    section_id BIGINT NULL,
    text VARCHAR(255) NOT NULL,
    completed SMALLINT NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_goals_owner ON goals (owner_type, owner_key, sort_order);

-- Maqsad QACHON bajarilgani. Statistika grafigida bajarilgan kun
-- yashil nuqta bilan belgilanadi (busiz sana ma'lum bo'lmasdi).
-- DIQQAT: izohda ham nuqta-vergul ishlatilmaydi, fayl shu belgi
-- bo'yicha bo'linadi va gap ikkiga bo'linib ketadi.
ALTER TABLE goals ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL;

CREATE INDEX IF NOT EXISTS idx_goals_folder ON goals (owner_type, owner_key, folder_id, sort_order);

CREATE INDEX IF NOT EXISTS idx_goals_section ON goals (owner_type, owner_key, folder_id, section_id, sort_order);

CREATE TABLE IF NOT EXISTS dictionary_words (
    id BIGSERIAL PRIMARY KEY,
    category VARCHAR(191) NOT NULL,
    word_ru VARCHAR(255) NOT NULL,
    word_uz VARCHAR(255) NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE dictionary_words ADD COLUMN IF NOT EXISTS lang VARCHAR(16) NOT NULL DEFAULT 'russian';

CREATE INDEX IF NOT EXISTS idx_dictionary_words_category_sort ON dictionary_words (lang, category, sort_order);

CREATE TABLE IF NOT EXISTS dictionary_mistakes (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    category VARCHAR(191) NOT NULL,
    word_ru VARCHAR(255) NOT NULL,
    word_uz VARCHAR(255) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_dictionary_mistakes_owner_word UNIQUE (owner_type, owner_key, category, word_ru)
);

ALTER TABLE dictionary_mistakes ADD COLUMN IF NOT EXISTS lang VARCHAR(16) NOT NULL DEFAULT 'russian';

CREATE INDEX IF NOT EXISTS idx_dictionary_mistakes_owner ON dictionary_mistakes (owner_type, owner_key, category);

-- Xatolar (dictionary_mistakes) ro'yxatining GitHub'dagi kabi versiya tarixi.
-- Har "yuklab olish" bosilganda joriy ro'yxat shu yerga bir nusxa qilib
-- yoziladi (o'chirilib ketmaydi) — foydalanuvchi istalgan eski versiyani
-- qayta ochib, o'sha so'zlar bilan yana mashq qila oladi.
CREATE TABLE IF NOT EXISTS dictionary_mistake_snapshots (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    lang VARCHAR(16) NOT NULL,
    word_count INT NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dict_mistake_snap ON dictionary_mistake_snapshots (owner_type, owner_key, lang, created_at DESC);

-- Testlardagi xato savollarning versiya tarixi (lug'atdagi bilan bir xil g'oya).
-- Savolning MATNI ham nusxaga yoziladi: savol keyinroq tahrirlansa yoki
-- o'chirilsa, eski versiya baribir o'sha paytdagi holatni ko'rsatadi.
CREATE TABLE IF NOT EXISTS quiz_wrong_snapshots (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    base_full_name VARCHAR(255) NOT NULL,
    question_count INT NOT NULL DEFAULT 0,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quiz_wrong_snap ON quiz_wrong_snapshots (owner_type, owner_key, base_full_name, created_at DESC);

CREATE TABLE IF NOT EXISTS language_topics (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    lang VARCHAR(16) NOT NULL,
    name VARCHAR(191) NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_language_topics_owner ON language_topics (owner_type, owner_key, lang, sort_order);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    first_name VARCHAR(191) DEFAULT NULL,
    username VARCHAR(191) DEFAULT NULL,
    birth_date DATE DEFAULT NULL,
    step VARCHAR(191) DEFAULT NULL,
    temp_data TEXT DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_boostday_users_chat_id UNIQUE (chat_id)
);

CREATE TABLE IF NOT EXISTS user_channels (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    channel_id VARCHAR(191) NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    channel_username VARCHAR(191) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_boostday_user_channel UNIQUE (user_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_boostday_user_channels_user ON user_channels (user_id);

-- Kanal qaysi MAVZUga tayinlangan (masalan 'sport', 'english', 'russian').
-- Bo'sh — umumiy kanal, mavzu tayinlanmagan. Sport bo'limidan mashq yuborilganda
-- shu maydon orqali to'g'ri kanal avtomatik tanlanadi.
-- ESKI ustun (bitta kanal = bitta mavzu) — endi ishlatilmaydi, `topics`ga
-- almashtirildi (bitta kanal bir nechta mavzuga ega bo'lishi mumkin). O'chirilmadi,
-- chunki eski qiymat allaqachon `topics`ga bir martalik ko'chirilgan (2026-08-03).
ALTER TABLE user_channels ADD COLUMN IF NOT EXISTS topic VARCHAR(32) NOT NULL DEFAULT '';

-- Vergul bilan ajratilgan mavzular ro'yxati (masalan "sport,russian") — bitta
-- kanal bir nechta mavzuga tayinlanishi mumkin, lekin har mavzu faqat BITTA
-- kanalga tegishli bo'ladi (yo'naltirish uchun — qaysi mavzudan yuborilsa,
-- aniq bitta kanalga borishi kerak).
ALTER TABLE user_channels ADD COLUMN IF NOT EXISTS topics VARCHAR(191) NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS plans (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    channel_id VARCHAR(191) NOT NULL,
    channel_name VARCHAR(255) DEFAULT NULL,
    plan_type VARCHAR(64) NOT NULL,
    content_type VARCHAR(64) DEFAULT NULL,
    file_id VARCHAR(500) DEFAULT NULL,
    caption TEXT DEFAULT NULL,
    items TEXT DEFAULT NULL,
    time VARCHAR(16) DEFAULT NULL,
    date DATE DEFAULT NULL,
    start_date DATE DEFAULT NULL,
    end_date DATE DEFAULT NULL,
    last_run TIMESTAMP DEFAULT NULL,
    next_run_at TIMESTAMP DEFAULT NULL,
    message_id BIGINT DEFAULT NULL,
    report_sent SMALLINT NOT NULL DEFAULT 0,
    tasks TEXT DEFAULT NULL,
    week_mode VARCHAR(16) NOT NULL DEFAULT 'everyday',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_boostday_plans_owner ON plans (owner_id, status, plan_type);

CREATE INDEX IF NOT EXISTS idx_boostday_plans_next_run ON plans (status, plan_type, next_run_at);

CREATE INDEX IF NOT EXISTS idx_boostday_plans_channel ON plans (channel_id);

CREATE TABLE IF NOT EXISTS history (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    total_tasks INT NOT NULL DEFAULT 0,
    completed_tasks INT NOT NULL DEFAULT 0,
    last_channel_id VARCHAR(191) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_boostday_history_day UNIQUE (user_id, year, month, day)
);

CREATE INDEX IF NOT EXISTS idx_boostday_history_user ON history (user_id, year, month, day);

CREATE TABLE IF NOT EXISTS settings (
    id BIGSERIAL PRIMARY KEY,
    setting_key VARCHAR(191) NOT NULL,
    setting_value TEXT DEFAULT NULL,
    CONSTRAINT uq_boostday_settings_key UNIQUE (setting_key)
);

CREATE TABLE IF NOT EXISTS sent_logs (
    id BIGSERIAL PRIMARY KEY,
    plan_id BIGINT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note VARCHAR(255) DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_boostday_sent_logs_plan_note ON sent_logs (plan_id, note);

-- Test natijalari tarixi (har bir yakunlangan sessiya)
CREATE TABLE IF NOT EXISTS quiz_results (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    base_full VARCHAR(191) NOT NULL,
    mode VARCHAR(32) NOT NULL DEFAULT '',
    total INT NOT NULL DEFAULT 0,
    correct INT NOT NULL DEFAULT 0,
    wrong INT NOT NULL DEFAULT 0,
    percent INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quiz_results_owner ON quiz_results (owner_type, owner_key, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_quiz_results_base ON quiz_results (owner_type, owner_key, base_full, created_at DESC);

-- Xato javoblar hisobi: flag_type ('saved') bilan aralashmasligi uchun alohida ustun
ALTER TABLE quiz_progress ADD COLUMN IF NOT EXISTS wrong_count INT NOT NULL DEFAULT 0;

-- Grammar mavzulariga test va o'yin biriktirish
ALTER TABLE language_topics ADD COLUMN IF NOT EXISTS test_content TEXT NOT NULL DEFAULT '';

ALTER TABLE language_topics ADD COLUMN IF NOT EXISTS game_content TEXT NOT NULL DEFAULT '';

ALTER TABLE language_topics ADD COLUMN IF NOT EXISTS game_type VARCHAR(16) NOT NULL DEFAULT 'fill';

-- Mavzu papkasi. Foydalanuvchi "Zamonlar/Present Simple" deb yozsa, "Zamonlar"
-- papkasi ochilib, ichiga "Present Simple" mavzusi tushadi.
-- MUHIM: papka ALOHIDA ustunda saqlanadi, nom ichida emas — chunki mavzu
-- nomining o'zida ham "/" bo'lishi mumkin ("идти / ходить", "Этот/эта/это/эти")
-- va nomni ajratib olishga urinish ularni noto'g'ri papkaga bo'lib yuborardi.
ALTER TABLE language_topics ADD COLUMN IF NOT EXISTS folder VARCHAR(191) NOT NULL DEFAULT '';

-- Materiallar bo'limlari (Reading/Listening/Writing/Speaking va h.k.) `lang`
-- ustunida "en_reading", "ru_shadowing" kabi kalitlar bilan saqlanadi —
-- VARCHAR(16) ularga tor bo'lib qolmasin. `folder` esa endi ICHMA-ICH yo'l
-- ("Level 1/Unit 2") bo'lishi mumkin: yo'l frontenddan ANIQ uzatiladi,
-- shuning uchun nom ichidagi "/" hech qachon papka deb talqin qilinmaydi.
ALTER TABLE language_topics ALTER COLUMN lang TYPE VARCHAR(64);

-- LMS (lms.tuit.uz) hisobi. Parol Fernet bilan SHIFRLANGAN holda saqlanadi va
-- hech qachon mijozga qaytarilmaydi (handlers/lms.py::_public). localStorage'ga
-- yozilmaydi — u brauzerga va sinxronga tushib ketardi.
CREATE TABLE IF NOT EXISTS lms_account (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    login VARCHAR(64) NOT NULL,
    password_enc TEXT NOT NULL,
    student_name VARCHAR(191) NOT NULL DEFAULT '',
    semester_id INT NOT NULL DEFAULT 0,
    semester_name VARCHAR(191) NOT NULL DEFAULT '',
    semesters TEXT NOT NULL DEFAULT '[]',
    auto_sync BOOLEAN NOT NULL DEFAULT TRUE,
    last_sync VARCHAR(32) NOT NULL DEFAULT '',
    last_error VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_lms_account_owner UNIQUE (owner_type, owner_key)
);

-- LMS'dan tortilgan dars jadvali. Har sinxronda TO'LIQ almashtiriladi —
-- haqiqat manbai LMS, mahalliy tahrir bu jadvalda saqlanmaydi (foydalanuvchi
-- o'z kurs/ish vaqtlarini Kun hisobidagi alohida saqlashda yuritadi).
CREATE TABLE IF NOT EXISTS lms_schedule (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    lesson_date DATE NOT NULL,
    start_time VARCHAR(5) NOT NULL,
    end_time VARCHAR(5) NOT NULL,
    subject VARCHAR(191) NOT NULL,
    stream VARCHAR(191) NOT NULL DEFAULT '',
    room VARCHAR(64) NOT NULL DEFAULT '',
    type_name VARCHAR(64) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lms_schedule_owner_date
    ON lms_schedule (owner_type, owner_key, lesson_date);

-- Savolga IXTIYORIY izoh: javob berilgandan keyin ko'rsatiladi (nega shu javob
-- to'g'ri ekanini tushuntirish). Bo'sh bo'lishi mumkin — izohsiz testlar
-- avvalgidek ishlayveradi.
ALTER TABLE quiz_questions ADD COLUMN IF NOT EXISTS explanation TEXT NOT NULL DEFAULT '';

-- Mashq turi: nima oshadi (og'irlik / takror / vaqt) va qaysi kunlari oshadi
ALTER TABLE sport_exercises ADD COLUMN IF NOT EXISTS progress_type VARCHAR(16) NOT NULL DEFAULT 'weight';

ALTER TABLE sport_exercises ADD COLUMN IF NOT EXISTS progress_mode VARCHAR(16) NOT NULL DEFAULT 'daily';

ALTER TABLE sport_exercises ADD COLUMN IF NOT EXISTS start_date DATE DEFAULT NULL;

-- Ro'yxatdagi tartib. Ilgari mashqlar faqat `id` bo'yicha chiqardi, ya'ni
-- yangi qo'shilgani DOIM eng pastga tushardi va tartibni o'zgartirib
-- bo'lmasdi. Kichik qiymat — yuqorida. Standart 0, shuning uchun mavjud
-- mashqlar tartibi o'zgarmaydi; tepaga chiqarish uchun manfiy qiymat.
ALTER TABLE sport_exercises ADD COLUMN IF NOT EXISTS sort_order INT NOT NULL DEFAULT 0;

-- Faoliyat jurnali: barcha bo'limlarda qilingan ishning yagona yozuvi (Tarix/Grafik/Heatmap
-- bo'limlari shunga tayanadi). Har qator — bitta voqea (test yakunlandi, mashq belgilandi,
-- mavzu o'qildi va h.k.), UI'da kun/bo'lim bo'yicha guruhlanadi va yig'iladi.
CREATE TABLE IF NOT EXISTS activity_log (
    id BIGSERIAL PRIMARY KEY,
    owner_type VARCHAR(32) NOT NULL,
    owner_key VARCHAR(191) NOT NULL,
    section VARCHAR(32) NOT NULL,
    object_name VARCHAR(255) NOT NULL DEFAULT '',
    amount DECIMAL(10,2) DEFAULT NULL,
    unit VARCHAR(32) NOT NULL DEFAULT '',
    duration_seconds INT DEFAULT NULL,
    meta TEXT DEFAULT NULL,
    occurred_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_activity_log_owner_date ON activity_log (owner_type, owner_key, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_activity_log_owner_section ON activity_log (owner_type, owner_key, section, occurred_at DESC);

-- Maqsad hajmi: katta / orta / kichik. Halqa shu uchta bo'yicha rangga bo'linadi.
-- Mavjud maqsadlar standart 'orta' bo'lib qoladi (migratsiya shart emas — DEFAULT).
ALTER TABLE goals ADD COLUMN IF NOT EXISTS size VARCHAR(8) NOT NULL DEFAULT 'orta';

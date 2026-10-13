# 02 — Ma'lumotlar modeli (PostgreSQL 16)

Quyida sxemaning mantiqiy loyihasi. Bu hali migratsiya emas — kod bosqichida Alembic
migratsiyalariga aylantiriladi.

---

## 1. `countries` — davlatlar

Xarita bilan katalogni bog'lovchi markaziy jadval. **Yagona haqiqat manbasi.**

```sql
CREATE TABLE countries (
    iso2            CHAR(2)      PRIMARY KEY,         -- 'UZ'
    iso3            CHAR(3)      NOT NULL,            -- 'UZB'
    m49             SMALLINT     NOT NULL UNIQUE,     -- 860 — XARITA KALITI
    name_en         TEXT         NOT NULL,            -- 'Uzbekistan'
    name_uz         TEXT         NOT NULL,            -- 'O'zbekiston'
    name_native     TEXT,
    slug            TEXT         NOT NULL UNIQUE,     -- 'uzbekistan'
    continent       TEXT         NOT NULL,            -- 'Asia'
    flag_emoji      TEXT,                             -- '🇺🇿'
    centroid_lat    DOUBLE PRECISION,                 -- globusni markazlashtirish uchun
    centroid_lon    DOUBLE PRECISION,
    bbox            DOUBLE PRECISION[4],              -- zoom-to-country uchun
    -- denormalizatsiya (worker yangilaydi, choropleth uchun)
    radio_count     INTEGER      NOT NULL DEFAULT 0,
    tv_count        INTEGER      NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

### ⚠️ Nozik nuqta: nega `m49` kerak?

Natural Earth GeoJSON/TopoJSON ma'lumotlarida `ISO_A2` maydoni **ba'zi davlatlarda
`-99`** bo'lib chiqadi (Fransiya, Norvegiya, Kosovo va boshqalar — versiyaga qarab).
Agar xaritani `iso2` bo'yicha bog'lasak, bu davlatlar bosilmaydigan bo'lib qoladi va
sababini topish qiyin bo'ladi.

**Yechim:** xarita bilan bog'lanish **raqamli M49 kodi** bo'yicha amalga oshiriladi
(`world-atlas / countries-110m` da aynan shu raqamli id ishlatiladi), `iso2` esa
ichki biznes-mantiq va URL uchun qoladi.

---

## 2. `channels` — kanallar (radio va TV)

```sql
CREATE TYPE channel_type AS ENUM ('radio', 'tv');

CREATE TABLE channels (
    id              BIGSERIAL    PRIMARY KEY,
    type            channel_type NOT NULL,
    name            TEXT         NOT NULL,
    slug            TEXT         NOT NULL,
    logo_url        TEXT,
    homepage        TEXT,
    languages       TEXT[]       NOT NULL DEFAULT '{}',   -- ['uz','ru']
    tags            TEXT[]       NOT NULL DEFAULT '{}',   -- ['news','pop','talk']
    bitrate_max     SMALLINT,                             -- kbps, ko'rsatish uchun
    -- tashqi manba identifikatorlari
    source          TEXT         NOT NULL,                -- 'radio-browser' | 'iptv-org' | 'manual'
    external_ids    JSONB        NOT NULL DEFAULT '{}',   -- {"radiobrowser_uuid": "..."}
    -- holat
    is_archived     BOOLEAN      NOT NULL DEFAULT FALSE,
    popularity      INTEGER      NOT NULL DEFAULT 0,      -- ichki reyting
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (type, slug)
);

CREATE INDEX idx_channels_type_popularity ON channels (type, popularity DESC)
    WHERE is_archived = FALSE;
CREATE INDEX idx_channels_tags ON channels USING GIN (tags);
CREATE INDEX idx_channels_external ON channels USING GIN (external_ids);
```

---

## 3. `channel_countries` — ko'pga-ko'p bog'lanish

### ⚠️ Nozik nuqta: nega `channels.country_iso2` yetmaydi?

Ko'p kanallar bir nechta davlatga tegishli: Euronews, Al Jazeera, BBC World Service,
diaspora radiolari. Agar bitta `country_iso2` ustuni qo'ysak, keyinchalik ko'chirish
og'riqli bo'ladi. Boshidan ko'pga-ko'p qilish kerak.

```sql
CREATE TABLE channel_countries (
    channel_id    BIGINT   NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    country_iso2  CHAR(2)  NOT NULL REFERENCES countries(iso2),
    is_primary    BOOLEAN  NOT NULL DEFAULT FALSE,   -- asosiy davlat (URL uchun)
    PRIMARY KEY (channel_id, country_iso2)
);

CREATE INDEX idx_cc_country ON channel_countries (country_iso2);
-- Har kanalda faqat bitta asosiy davlat bo'lishi kafolatlanadi:
CREATE UNIQUE INDEX idx_cc_one_primary ON channel_countries (channel_id)
    WHERE is_primary;
```

---

## 4. `streams` — oqim havolalari

Bitta kanalda bir nechta oqim bo'lishi mumkin (turli sifat, zaxira havolalar).

```sql
CREATE TYPE stream_kind AS ENUM ('mp3', 'aac', 'ogg', 'hls', 'dash');

CREATE TABLE streams (
    id              BIGSERIAL    PRIMARY KEY,
    channel_id      BIGINT       NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    url             TEXT         NOT NULL,
    url_resolved    TEXT,                             -- redirectlardan keyingi haqiqiy URL
    kind            stream_kind  NOT NULL,
    bitrate         SMALLINT,
    priority        SMALLINT     NOT NULL DEFAULT 0,  -- kichik raqam = avval sinab ko'riladi

    -- health checker aniqlagan IMKONIYATLAR (eng muhim ustunlar)
    is_https        BOOLEAN,
    sends_cors      BOOLEAN,
    is_geo_blocked  BOOLEAN,
    needs_proxy     BOOLEAN      NOT NULL DEFAULT TRUE,

    -- health checker aniqlagan HOLAT (denormalizatsiya)
    last_ok_at      TIMESTAMPTZ,
    last_check_at   TIMESTAMPTZ,
    fail_count      SMALLINT     NOT NULL DEFAULT 0,
    score           SMALLINT     NOT NULL DEFAULT 50, -- 0..100 ishonchlilik
    latency_ms      INTEGER,

    is_archived     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (channel_id, url)
);

-- Frontend uchun asosiy so'rov: ishlaydigan oqimlar
CREATE INDEX idx_streams_playable ON streams (channel_id, priority, score DESC)
    WHERE is_archived = FALSE AND score > 20;

-- Health checker navbati uchun
CREATE INDEX idx_streams_check_queue ON streams (last_check_at NULLS FIRST)
    WHERE is_archived = FALSE;
```

---

## 5. `stream_checks` — tekshiruv tarixi (vaqt qatori)

```sql
CREATE TABLE stream_checks (
    id            BIGSERIAL,
    stream_id     BIGINT       NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
    checked_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    ok            BOOLEAN      NOT NULL,
    http_status   SMALLINT,
    latency_ms    INTEGER,
    error         TEXT,
    PRIMARY KEY (id, checked_at)
) PARTITION BY RANGE (checked_at);
```

### ⚠️ Nozik nuqta: partitioning majburiy

50 000 oqim × kuniga ~10 tekshiruv = **oyiga 15 million qator**. Partitioning bo'lmasa
bu jadval 6 oyda bazani bo'g'ib qo'yadi. Oylik partition + 3 oydan keyin `DROP PARTITION`
(yoki agregatlangan holda arxivlash).

Alternativa: `pg_partman` yoki TimescaleDB. MVP uchun oddiy oylik partition yetarli.

---

## 6. `play_events` — ijro statistikasi

Real vaqtda Redis'da sanaladi (`INCR play:{stream_id}:{sana}`), worker har 5 daqiqada
PostgreSQL ga quyadi. Har bosishni darhol DB ga yozish — keraksiz yuk.

```sql
CREATE TABLE play_stats_daily (
    channel_id    BIGINT   NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    country_iso2  CHAR(2),                       -- TINGLOVCHI davlati (GeoIP), kanal emas
    day           DATE     NOT NULL,
    plays         INTEGER  NOT NULL DEFAULT 0,
    PRIMARY KEY (channel_id, country_iso2, day)
);
```

`channels.popularity` shu jadvaldan hisoblanadi: oxirgi 7 kunlik ijro soni.

---

## 7. `sources` — ingest manbalari registri

```sql
CREATE TABLE sources (
    name            TEXT         PRIMARY KEY,   -- 'radio-browser'
    base_url        TEXT         NOT NULL,
    last_sync_at    TIMESTAMPTZ,
    last_sync_ok    BOOLEAN,
    last_cursor     TEXT,                       -- inkremental sinxronizatsiya uchun
    items_total     INTEGER,
    notes           TEXT
);
```

---

## 8. Foydalanuvchilar (3-bosqich, hozir kerak emas)

```sql
CREATE TABLE users (
    id            BIGSERIAL    PRIMARY KEY,
    email         TEXT         UNIQUE,
    display_name  TEXT,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE favorites (
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel_id  BIGINT       NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, channel_id)
);
```

**Muhim:** MVP'da auth yo'q. Sevimlilar `localStorage` da saqlanadi — ro'yxatdan
o'tishni talab qilish radio saytida foydalanuvchini qo'rqitadi. Akkaunt keyin,
"qurilmalar orasida sinxronlash" ehtiyoji paydo bo'lganda qo'shiladi.

---

## 9. Qidiruv

MVP: PostgreSQL `pg_trgm` + `GIN` indeks. 50 000 qator uchun bu mutlaqo yetarli,
Elasticsearch keraksiz murakkablik.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_channels_name_trgm ON channels USING GIN (name gin_trgm_ops);
```

---

## 10. Yakuniy eslatma

Ikki narsa boshidan to'g'ri qilinishi kerak, keyin tuzatish qimmat:

1. **`channel_countries`** ko'pga-ko'p (bitta `country_iso2` ustuni emas)
2. **`stream_checks`** partitioning bilan

Qolgan hamma narsani keyin ham migratsiya qilish mumkin.

"""Boshlang'ich sxema: davlatlar, kanallar, oqimlar, tekshiruvlar

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-14
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Qidiruv uchun trigram indekslari (ilike '%...%' to'liq skanni almashtiradi)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ---------- countries ----------
    op.create_table(
        "countries",
        sa.Column("iso2", sa.String(5), primary_key=True),
        sa.Column("iso3", sa.String(3), nullable=False),
        sa.Column("m49", sa.SmallInteger, nullable=False, unique=True),
        sa.Column("name_en", sa.String, nullable=False),
        sa.Column("name_uz", sa.String, nullable=False),
        sa.Column("slug", sa.String, nullable=False, unique=True),
        sa.Column("continent", sa.String, nullable=False),
        sa.Column("flag_emoji", sa.String(16)),
        sa.Column("centroid_lat", sa.Float),
        sa.Column("centroid_lon", sa.Float),
        sa.Column("bbox", postgresql.JSONB),
        sa.Column("radio_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tv_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_countries_m49", "countries", ["m49"])
    op.create_index("ix_countries_slug", "countries", ["slug"])
    op.create_index("ix_countries_radio_count", "countries", ["radio_count"])

    # ---------- channels ----------
    op.create_table(
        "channels",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("type", sa.String(10), nullable=False, server_default="radio"),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("slug", sa.String, nullable=False),
        sa.Column("logo_url", sa.String),
        sa.Column("homepage", sa.String),
        sa.Column("languages", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("external_ids", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("bitrate_max", sa.SmallInteger),
        sa.Column("source", sa.String, nullable=False, server_default="radio-browser"),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("popularity", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("type", "slug", name="uq_channel_type_slug"),
    )
    op.create_index("ix_channels_name", "channels", ["name"])
    op.create_index("ix_channels_slug", "channels", ["slug"])
    op.create_index("ix_channels_is_archived", "channels", ["is_archived"])
    op.create_index(
        "ix_channels_type_popularity", "channels", ["type", "popularity"],
        postgresql_where=sa.text("is_archived = false"),
    )
    op.create_index("ix_channels_tags_gin", "channels", ["tags"], postgresql_using="gin")
    op.create_index("ix_channels_languages_gin", "channels", ["languages"], postgresql_using="gin")
    op.create_index("ix_channels_external_gin", "channels", ["external_ids"], postgresql_using="gin")
    # Nom bo'yicha tez qidiruv
    op.execute(
        "CREATE INDEX ix_channels_name_trgm ON channels USING gin (name gin_trgm_ops)"
    )

    # ---------- channel_countries ----------
    op.create_table(
        "channel_countries",
        sa.Column(
            "channel_id", sa.BigInteger,
            sa.ForeignKey("channels.id", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column(
            "country_iso2", sa.String(5),
            sa.ForeignKey("countries.iso2", ondelete="CASCADE"), primary_key=True,
        ),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_channel_countries_country", "channel_countries", ["country_iso2"])
    # Har kanalda ko'pi bilan bitta asosiy davlat
    op.create_index(
        "uq_channel_single_primary", "channel_countries", ["channel_id"],
        unique=True, postgresql_where=sa.text("is_primary = true"),
    )

    # ---------- streams ----------
    op.create_table(
        "streams",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "channel_id", sa.BigInteger,
            sa.ForeignKey("channels.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("url", sa.String, nullable=False),
        sa.Column("url_resolved", sa.String),
        sa.Column("format", sa.String(20)),
        sa.Column("bitrate", sa.SmallInteger),
        sa.Column("priority", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("is_https", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("sends_cors", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("is_geo_blocked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("needs_proxy", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_ok_at", sa.DateTime(timezone=True)),
        sa.Column("last_check_at", sa.DateTime(timezone=True)),
        sa.Column("next_check_at", sa.DateTime(timezone=True)),
        sa.Column("fail_count", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("score", sa.SmallInteger, nullable=False, server_default="50"),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("channel_id", "url", name="uq_stream_channel_url"),
    )
    op.create_index("ix_streams_channel_id", "streams", ["channel_id"])
    op.create_index(
        "ix_streams_playable", "streams", ["channel_id", "priority", "score"],
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("ix_streams_check_queue", "streams", ["next_check_at"])

    # ---------- stream_checks (partitsiyalangan) ----------
    # Bu jadval eng tez o'sadigan jadval. Partitsiyasiz u bir necha oyda
    # bazani bo'g'ib qo'yadi, eski yozuvlarni o'chirish esa og'ir DELETE
    # bo'lib qoladi. Oylik partitsiya bilan eskisini DROP qilish arzon.
    op.execute("""
        CREATE TABLE stream_checks (
            id          BIGSERIAL      NOT NULL,
            checked_at  TIMESTAMPTZ    NOT NULL DEFAULT now(),
            stream_id   BIGINT         NOT NULL REFERENCES streams(id) ON DELETE CASCADE,
            ok          BOOLEAN        NOT NULL DEFAULT false,
            status_code SMALLINT,
            latency_ms  INTEGER,
            error       VARCHAR(300),
            headers_seen JSONB         NOT NULL DEFAULT '{}'::jsonb,
            PRIMARY KEY (id, checked_at)
        ) PARTITION BY RANGE (checked_at)
    """)
    op.create_index("ix_stream_checks_stream_id", "stream_checks", ["stream_id"])
    op.create_index("ix_stream_checks_checked_at", "stream_checks", ["checked_at"])

    # Joriy oydan boshlab 6 oylik partitsiyalar + barcha boshqa sanalar uchun
    # "default" partitsiya (partitsiya yetishmay qolsa INSERT yiqilmasin)
    op.execute("""
        DO $$
        DECLARE
            start_month DATE := date_trunc('month', now())::date;
            i INT;
            p_start DATE;
            p_end DATE;
            p_name TEXT;
        BEGIN
            FOR i IN 0..5 LOOP
                p_start := start_month + (i || ' month')::interval;
                p_end   := p_start + INTERVAL '1 month';
                p_name  := 'stream_checks_' || to_char(p_start, 'YYYY_MM');
                EXECUTE format(
                    'CREATE TABLE IF NOT EXISTS %I PARTITION OF stream_checks
                     FOR VALUES FROM (%L) TO (%L)', p_name, p_start, p_end
                );
            END LOOP;
            CREATE TABLE IF NOT EXISTS stream_checks_default
                PARTITION OF stream_checks DEFAULT;
        END $$;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS stream_checks CASCADE")
    op.drop_table("streams")
    op.drop_table("channel_countries")
    op.drop_table("channels")
    op.drop_table("countries")

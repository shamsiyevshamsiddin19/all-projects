"""Baza qatlami (db.py) testlari."""

from __future__ import annotations

import pytest
from app.db import _split_statements


def test_split_simple_statements():
    sql = "CREATE TABLE a (id INT); CREATE TABLE b (id INT);"
    stmts = _split_statements(sql)
    assert stmts == ["CREATE TABLE a (id INT)", "CREATE TABLE b (id INT)"]


def test_split_with_comments_containing_semicolon():
    sql = """
    -- Birinchi izoh; ichida nuqta-vergul bor
    CREATE TABLE a (id INT);
    -- Ikkinchi izoh; yana bitta;
    CREATE TABLE b (id INT);
    """
    stmts = _split_statements(sql)
    assert len(stmts) == 2
    assert stmts[0] == "CREATE TABLE a (id INT)"
    assert stmts[1] == "CREATE TABLE b (id INT)"


def test_split_with_quotes_containing_semicolon():
    sql = """
    INSERT INTO t (val) VALUES ('salom; dunyo');
    INSERT INTO t (val) VALUES ('ikkinchi; ''qo''shtirnoq''; davom');
    """
    stmts = _split_statements(sql)
    assert len(stmts) == 2
    assert stmts[0] == "INSERT INTO t (val) VALUES ('salom; dunyo')"
    assert stmts[1] == "INSERT INTO t (val) VALUES ('ikkinchi; ''qo''shtirnoq''; davom')"


def test_split_with_dollar_quoted_do_block():
    sql = """
    CREATE TABLE activity_log (id BIGSERIAL PRIMARY KEY);
    DO $$ BEGIN
        ALTER TABLE activity_log ADD CONSTRAINT chk_activity_duration
            CHECK (duration_seconds IS NULL OR duration_seconds >= 0);
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    CREATE TABLE goals (id BIGSERIAL PRIMARY KEY);
    """
    stmts = _split_statements(sql)
    assert len(stmts) == 3
    assert stmts[0] == "CREATE TABLE activity_log (id BIGSERIAL PRIMARY KEY)"
    assert "DO $$ BEGIN" in stmts[1]
    assert "ALTER TABLE activity_log ADD CONSTRAINT chk_activity_duration" in stmts[1]
    assert "EXCEPTION WHEN duplicate_object THEN NULL;" in stmts[1]
    assert stmts[1].endswith("END $$")
    assert stmts[2] == "CREATE TABLE goals (id BIGSERIAL PRIMARY KEY)"


def test_split_with_tagged_dollar_quote():
    sql = """
    CREATE FUNCTION foo() RETURNS void AS $func$
    BEGIN
        SELECT 1;
        RETURN;
    END;
    $func$ LANGUAGE plpgsql;
    SELECT 2;
    """
    stmts = _split_statements(sql)
    assert len(stmts) == 2
    assert "CREATE FUNCTION foo()" in stmts[0]
    assert "$func$ LANGUAGE plpgsql" in stmts[0]
    assert stmts[1] == "SELECT 2"


def test_schema_sql_parses_all_do_blocks():
    from app.db import _resolve_schema_path, _split_statements

    p = _resolve_schema_path()
    assert p is not None, "schema.sql topilmadi"
    sql = p.read_text(encoding="utf-8")
    stmts = _split_statements(sql)
    assert len(stmts) > 70
    do_blocks = [s for s in stmts if s.startswith("DO $$")]
    assert len(do_blocks) == 12
    for b in do_blocks:
        assert b.endswith("END $$")
        assert "ALTER TABLE" in b
        assert "ADD CONSTRAINT" in b


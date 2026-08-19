"""app_storage bootstrap/sync/clear."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy import text

from .. import db
from ..errors import success
from ..owner import owner_context
from .common import s


def bootstrap(request: Request, body: dict):
    ctx = owner_context(request)
    return success({"items": db.storage_map(ctx)})


def sync(request: Request, body: dict):
    ctx = owner_context(request)
    ops = body.get("ops") if isinstance(body.get("ops"), list) else []

    with db.tx() as conn:
        for op in ops:
            if not isinstance(op, dict):
                continue
            key = s(op.get("key"))
            if key == "":
                continue
            op_type = s(op.get("type")) or "set"
            if op_type == "delete":
                conn.execute(
                    text("DELETE FROM app_storage WHERE owner_type = :ot AND owner_key = :ok AND storage_key = :sk"),
                    {"ot": ctx["owner_type"], "ok": ctx["owner_key"], "sk": key},
                )
            else:
                db.storage_set(key, str(op.get("value") or ""), ctx, conn=conn)

    return success({"count": len(ops)})


def clear(request: Request, body: dict):
    ctx = owner_context(request)
    db.execute(
        "DELETE FROM app_storage WHERE owner_type = :ot AND owner_key = :ok",
        {"ot": ctx["owner_type"], "ok": ctx["owner_key"]},
    )
    return success()

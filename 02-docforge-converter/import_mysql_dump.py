import asyncio
import os
import re
from core.database import db

async def migrate_data(sql_file_path: str):
    print("PostgreSQL bazasiga ulanilmoqda...")
    await db.connect()
    
    print(f"Fayl o'qilmoqda: {sql_file_path}")
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by statements
    statements = content.split(';')
    
    insert_queries = []
    for stmt in statements:
        stmt = stmt.strip()
        if stmt.startswith("INSERT INTO"):
            # PostgreSQL da jadvallar va ustunlar qo'shtirnoq bilan yoziladi
            # Shuning uchun MySQL dagi ` belgisini " ga almashtiramiz
            pg_stmt = stmt.replace('`', '"')
            # current_timestamp() -> CURRENT_TIMESTAMP
            pg_stmt = pg_stmt.replace('current_timestamp()', 'CURRENT_TIMESTAMP')
            insert_queries.append(pg_stmt)

    if not insert_queries:
        print("Hech qanday INSERT so'rovi topilmadi.")
        return

    print(f"Jami {len(insert_queries)} ta INSERT so'rovi topildi. Bajarilmoqda...")
    
    async with db.pool.acquire() as conn:
        for i, q in enumerate(insert_queries):
            try:
                await conn.execute(q)
                print(f"[{i+1}/{len(insert_queries)}] Muvaffaqiyatli!")
            except Exception as e:
                print(f"[{i+1}/{len(insert_queries)}] XATOLIK: {e}")
                # Kichik xatolarni (masalan, duplicate key) o'tkazib yuboramiz

    print("Ma'lumotlarni ko'chirish yakunlandi!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Foydalanish: python import_mysql_dump.py <sql_fayl_yo'li>")
        sys.exit(1)
        
    asyncio.run(migrate_data(sys.argv[1]))

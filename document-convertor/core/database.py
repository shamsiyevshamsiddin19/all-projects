import asyncpg
from core.config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME
        )
        await self.create_tables()

    async def create_tables(self):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                  chat_id BIGINT PRIMARY KEY,
                  full_name VARCHAR(255),
                  username VARCHAR(255),
                  mode VARCHAR(50),
                  last_msg_id INT,
                  admin_login_id INT,
                  finished BOOLEAN DEFAULT FALSE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  step VARCHAR(50),
                  temp_data TEXT,
                  lang VARCHAR(10) DEFAULT 'uz'
                );

                CREATE TABLE IF NOT EXISTS channels (
                  id SERIAL PRIMARY KEY,
                  channel_id VARCHAR(100) NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                  setting_key VARCHAR(50) PRIMARY KEY,
                  setting_value VARCHAR(255)
                );

                CREATE TABLE IF NOT EXISTS auto_delete (
                  id SERIAL PRIMARY KEY,
                  chat_id BIGINT NOT NULL,
                  message_id INT NOT NULL,
                  delete_time INT NOT NULL
                );
            ''')
            
            # Default setting
            await conn.execute('''
                INSERT INTO settings (setting_key, setting_value) 
                VALUES ('subscription_active', '0') 
                ON CONFLICT (setting_key) DO NOTHING;
            ''')

    async def get_user(self, chat_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("SELECT * FROM users WHERE chat_id = $1", chat_id)

    async def create_user(self, chat_id: int, full_name: str, username: str):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (chat_id, full_name, username) 
                VALUES ($1, $2, $3) ON CONFLICT DO NOTHING
            ''', chat_id, full_name, username)

    async def update_user(self, chat_id: int, **kwargs):
        if not kwargs:
            return
        set_clause = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        values = list(kwargs.values())
        async with self.pool.acquire() as conn:
            await conn.execute(f'''
                UPDATE users SET {set_clause} WHERE chat_id = $1
            ''', chat_id, *values)

    async def get_setting(self, key: str):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("SELECT setting_value FROM settings WHERE setting_key = $1", key)

    async def set_setting(self, key: str, value: str):
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO settings (setting_key, setting_value) 
                VALUES ($1, $2)
                ON CONFLICT (setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value
            ''', key, value)

    async def get_channels(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM channels")

    async def add_channel(self, channel_id: str):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO channels (channel_id) VALUES ($1)", channel_id)

    async def delete_channel(self, channel_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM channels WHERE id = $1", channel_id)

    async def get_all_chat_ids(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT chat_id FROM users")
            return [r['chat_id'] for r in rows]

    async def get_stats(self):
        async with self.pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM users")
            today = await conn.fetchval("SELECT COUNT(*) FROM users WHERE created_at >= NOW() - INTERVAL '1 DAY'")
            return {'total': total, 'today': today}

    async def add_auto_delete(self, chat_id: int, message_id: int, delete_time: int):
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT INTO auto_delete (chat_id, message_id, delete_time) VALUES ($1, $2, $3)", chat_id, message_id, delete_time)

    async def get_expired_messages(self, now: int):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM auto_delete WHERE delete_time <= $1", now)

    async def remove_auto_delete(self, record_id: int):
        async with self.pool.acquire() as conn:
            await conn.execute("DELETE FROM auto_delete WHERE id = $1", record_id)

db = Database()

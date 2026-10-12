import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Database URL: default to PostgreSQL peer auth, or env override
DEFAULT_DB_URL = "postgresql+psycopg2://@/blog_db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# JWT Secret & Settings
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-blog-jwt-key-change-in-production-198273645")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours

"""OneID orqali LMS'ga kirishni qo'lda tekshirish.

Ishga tushirish (parol ekranda ko'rinmaydi, hech qayerga yozilmaydi):

    .venv/bin/python -m scripts.smoke_oneid
"""
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lms.client import LmsClient, LmsError, LoginError, OneIdSmsRequired  # noqa: E402


async def main():
    login = input("OneID login (JSHSHIR/PINFL yoki foydalanuvchi nomi): ").strip()
    password = getpass.getpass("OneID parol (ko'rinmaydi): ")

    async with LmsClient() as c:
        print("\n[1] LMS → SSO → id.egov.uz zanjiri…")
        tid, cid = await c._oneid_start()
        print(f"    OK  token_id={tid}  client_id={cid}")

        print("[2] OneID autentifikatsiya…")
        try:
            await c.oneid_login(login, password)
        except OneIdSmsRequired:
            code = input("    SMS kod keldi, kiriting: ").strip()
            await c.oneid_login_sms(login, code)
        except LoginError as e:
            print(f"    XATO: {e}")
            return
        except LmsError as e:
            print(f"    XATO: {e}")
            return
        print("    OK  LMS sessiya ochildi")

        print("[3] Profil o'qilyapti…")
        p = await c.profile()
        print(f"    {p.full_name} | {p.group} | {p.level}-kurs | {p.speciality}")

        print("[4] Fanlar…")
        courses = await c.courses()
        print(f"    {len(courses)} ta fan: " + ", ".join(x.subject for x in courses[:3]))

    print("\n✅ OneID oqimi to'liq ishlayapti.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

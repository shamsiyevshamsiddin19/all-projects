"""TMDB qidiruvi — bot bazasida topilmagan kinolarni internetdan izlash."""
import aiohttp

import config

_BASE = "https://api.themoviedb.org/3/search/multi"
_IMG = "https://image.tmdb.org/t/p/w500"


def _format_item(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "name": item.get("title") or item.get("name") or "Noma'lum",
        "type": "movie" if item.get("media_type") == "movie" else "series",
        "source": "tmdb",
        "overview": item.get("overview") or "Tavsif mavjud emas.",
        "poster": (_IMG + item["poster_path"]) if item.get("poster_path") else None,
        "year": (item.get("release_date") or item.get("first_air_date") or "")[:4],
        "rating": item.get("vote_average") or 0,
    }


async def search(query: str, limit: int = 10) -> list[dict]:
    if not config.TMDB_KEY or len(config.TMDB_KEY) < 5:
        return []

    results: list[dict] = []
    found_ids: set[int] = set()
    headers = {"Authorization": f"Bearer {config.TMDB_KEY}", "accept": "application/json"}

    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        for lang in ("uz-UZ", "ru-RU", "en-US"):
            if len(results) >= limit:
                break
            params = {"query": query, "language": lang, "include_adult": "false"}
            try:
                async with session.get(_BASE, params=params) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
            except Exception:
                continue

            for item in data.get("results", []):
                if len(results) >= limit:
                    break
                if item.get("id") in found_ids:
                    continue
                if item.get("media_type") not in ("movie", "tv"):
                    continue
                results.append(_format_item(item))
                found_ids.add(item["id"])

    return results

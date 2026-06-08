from __future__ import annotations
import json
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

MANGADEX_BASE = "https://api.mangadex.org"
MANGADEX_CDN  = "https://uploads.mangadex.org"
LANG_PRIORITY = ["fr", "en", "ja-ro", "ja"]


def _pick_translation(translations: dict, priority: list[str] = LANG_PRIORITY) -> Optional[str]:
    for lang in priority:
        if translations.get(lang):
            return translations[lang]
    return next(iter(translations.values()), None)


def _build_cover_url(manga_id: str, filename: str) -> str:
    return f"{MANGADEX_CDN}/covers/{manga_id}/{filename}.256.jpg"


async def fetch_manga_detail(manga_id: str) -> dict | None:
    params = {
        "includes[]": ["cover_art", "author", "artist"],
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"{MANGADEX_BASE}/manga/{manga_id}",
                params=params,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error("MangaDex HTTP error %s pour %s", e.response.status_code, manga_id)
            raise
        except httpx.RequestError as e:
            logger.error("MangaDex unreachable: %s", e)
            raise

    data = resp.json().get("data", {})
    if not data:
        return None

    attrs = data.get("attributes", {})
    relationships = data.get("relationships", [])
    titles: dict = attrs.get("title", {})
    alt_titles: list[dict] = attrs.get("altTitles", [])
    all_titles: dict = {}
    for alt in alt_titles:
        all_titles.update(alt)
    all_titles.update(titles)
    title_fr = all_titles.get("fr") or all_titles.get("fr-fr")
    title_en = all_titles.get("en")
    title_original = (
        all_titles.get("ja-ro")
        or all_titles.get("ja")
        or all_titles.get("ko")
        or all_titles.get("zh")
        or _pick_translation(all_titles)
        or "Titre inconnu"
    )

    description_map: dict = attrs.get("description", {})
    description = _pick_translation(description_map)
    tags = attrs.get("tags", [])
    genres = [
        _pick_translation(t["attributes"]["name"]) or ""
        for t in tags
        if t.get("attributes", {}).get("group") == "genre"
    ]
    author_names = [
        rel["attributes"]["name"]
        for rel in relationships
        if rel.get("type") in ("author", "artist") and rel.get("attributes")
    ]
    author_names = list(dict.fromkeys(author_names))
    cover_url: Optional[str] = None
    for rel in relationships:
        if rel.get("type") == "cover_art" and rel.get("attributes"):
            filename = rel["attributes"].get("fileName", "")
            if filename:
                cover_url = _build_cover_url(manga_id, filename)
            break

    return {
        "id": manga_id,
        "title_fr": title_fr,
        "title_en": title_en,
        "title_original": title_original,
        "description": description,
        "cover_url": cover_url,
        "author_names": json.dumps(author_names, ensure_ascii=False),
        "genres": json.dumps(genres, ensure_ascii=False),
        "status": attrs.get("status"),
        "year": attrs.get("year"),
        "content_rating": attrs.get("contentRating"),
    }


async def search_manga(
    query: str,
    limit: int = 20,
    offset: int = 0,
    genres: list[str] | None = None,
    year: int | None = None,
    status: str | None = None,
) -> dict:
    params: dict = {
        "title": query,
        "limit": limit,
        "offset": offset,
        "includes[]": ["cover_art", "author"],
        "availableTranslatedLanguage[]": ["fr", "en"],
        "order[relevance]": "desc",
    }
    if year:
        params["year"] = year
    if status:
        params["status[]"] = status
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{MANGADEX_BASE}/manga", params=params)
        resp.raise_for_status()

    payload = resp.json()
    results = []

    for item in payload.get("data", []):
        mid = item["id"]
        attrs = item.get("attributes", {})
        relationships = item.get("relationships", [])
        titles = attrs.get("title", {})
        alt_titles_list = attrs.get("altTitles", [])
        all_t: dict = {}
        for a in alt_titles_list:
            all_t.update(a)
        all_t.update(titles)
        cover_url = None
        for rel in relationships:
            if rel.get("type") == "cover_art" and rel.get("attributes"):
                fn = rel["attributes"].get("fileName", "")
                if fn:
                    cover_url = _build_cover_url(mid, fn)
                break
        tags = attrs.get("tags", [])
        genres_list = [
            _pick_translation(t["attributes"]["name"]) or ""
            for t in tags
            if t.get("attributes", {}).get("group") == "genre"
        ]
        results.append({
            "id": mid,
            "title": _pick_translation(all_t) or "?",
            "cover_url": cover_url,
            "year": attrs.get("year"),
            "status": attrs.get("status"),
            "genres": genres_list,
        })
    return {
        "results": results,
        "total": payload.get("total", len(results)),
        "offset": offset,
        "limit": limit,
    }

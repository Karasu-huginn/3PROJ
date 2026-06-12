from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import urllib.request
import urllib.parse
import json

# -*- coding: utf-8 -*-
router = APIRouter()

CACHE_DURATION_MINUTES = 10
search_cache = {}

def get_cached_data(cache_key: str):
    if cache_key in search_cache:
        item = search_cache[cache_key]
        if datetime.now() < item["expires_at"]:
            return item["data"]
        else:
            del search_cache[cache_key]
    return None

def set_cached_data(cache_key: str, data: list):
    search_cache[cache_key] = {
        "data": data,
        "expires_at": datetime.now() + timedelta(minutes=CACHE_DURATION_MINUTES)
    }

# ==========================================
# ROUTE DE RECHERCHE MANGADEX (SANS HTTPX)
# ==========================================
MANGADEX_API_URL = "https://api.mangadex.org"

@router.get('/search/manga')
def search_manga(
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    genre: Optional[str] = Query(None),
    year: Optional[int] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    # 1. Clé de cache
    cache_key = f"search_{title}_{author}_{genre}_{year}_{limit}_{offset}"
    cached_response = get_cached_data(cache_key)
    if cached_response:
        return {"source": "cache", "results": cached_response}

    # 2. Construction des paramètres de l'URL
    params = {
        "limit": limit,
        "offset": offset,
        "includes[]": ["cover_art", "author"]
    }
    
    if title:
        params["title"] = title
    if year:
        params["year"] = year
        
    if genre:
        genres_mapping = {
            "Action": "391b0423-db2f-4516-8479-badb69990820",
            "Aventure": "87ccb865-1741-4311-8e78-5e59111b3ca4",
            "Drame": "b9af3a63-f058-434a-9e60-e8e51d30e4b2"
        }
        if genre in genres_mapping:
            params["includedTags[]"] = genres_mapping[genre]

    # Encodage des paramètres pour l'URL (ex: ?limit=10&offset=0...)
    query_string = urllib.parse.urlencode(params, doseq=True)
    full_url = f"{MANGADEX_API_URL}/manga?{query_string}"

    # 3. Appel à l'API MangaDex via l'outil natif de Python (urllib)
    try:
        # On ajoute un "User-Agent" pour faire croire à MangaDex qu'on est un navigateur classique (ils bloquent parfois les requêtes Python vides)
        req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
            data = json.loads(html)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"L'API externe MangaDex est indisponible ou l'appel a échoué.")

    # 4. Formatage des résultats pour ton React
    formatted_results = []
    for item in data.get("data", []):
        attributes = item.get("attributes", {})
        manga_title = attributes.get("title", {}).get("en") or list(attributes.get("title", {}).values())[0]
        synopsis = attributes.get("description", {}).get("fr") or attributes.get("description", {}).get("en") or "Aucun synopsis disponible."
        
        author_name = "Auteur inconnu"
        cover_filename = ""
        
        for rel in item.get("relationships", []):
            if rel.get("type") == "author" and "attributes" in rel:
                author_name = rel["attributes"].get("name", author_name)
            if rel.get("type") == "cover_art" and "attributes" in rel:
                cover_filename = rel["attributes"].get("fileName", "")

        cover_url = f"https://uploads.mangadex.org/covers/{item['id']}/{cover_filename}" if cover_filename else "https://placehold.co/200x300?text=Pas+d+image"
        genres = [tag.get("attributes", {}).get("name", {}).get("en") for tag in attributes.get("tags", [])]

        formatted_results.append({
            "id": item["id"],
            "title": manga_title,
            "author": author_name,
            "genre": genres,
            "year": attributes.get("year"),
            "synopsis": synopsis,
            "coverUrl": cover_url
        })

    set_cached_data(cache_key, formatted_results)
    return {"source": "api", "results": formatted_results}
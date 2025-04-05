from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx
from bs4 import BeautifulSoup
from typing import List
import re
import asyncio

app = FastAPI()

TMDB_API = "3a08a646f83edac9a48438ac670a78b2"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Utility Functions

def parse_quality(title):
    match = re.search(r'(480p|720p|1080p|2160p)', title)
    return match.group(1) if match else "Unknown"

def parse_language(title):
    title = title.lower()
    if "tamil" in title:
        return "Tamil"
    if "hindi" in title:
        return "Hindi"
    if "telugu" in title:
        return "Telugu"
    if "malayalam" in title:
        return "Malayalam"
    if "english" in title:
        return "English"
    return "Unknown"

# Fetch movie links using DuckDuckGo search
async def fetch_duckduckgo(site: str, query: str):
    url = f"https://html.duckduckgo.com/html?q=site:{site} {query}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for link in soup.select(".result__a")[:5]:
        href = link['href']
        if "login" not in href.lower():
            results.append({
                "source": site.split('.')[0],
                "title": link.text,
                "link": href,
                "quality": parse_quality(link.text),
                "language": parse_language(link.text)
            })
    return results

# Fetch movie details from TMDB API
async def fetch_tmdb(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API}&query={query}"
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
    data = res.json()
    if data['results']:
        movie = data['results'][0]
        return {
            "title": movie['title'],
            "year": movie['release_date'].split("-")[0] if movie.get("release_date") else "",
            "rating": movie.get("vote_average"),
            "overview": movie.get("overview"),
            "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}",
            "tmdb_link": f"https://www.themoviedb.org/movie/{movie['id']}"
        }
    return {}

@app.get("/")
async def root():
    return {"message": "Welcome to Zero Super Movie API with Quality & Language!"}

@app.get("/search")
async def search_movie(q: str = Query(...)):
    tmdb_data = await fetch_tmdb(q)
    tasks = [
        fetch_duckduckgo("filmxy.vip", q),
        fetch_duckduckgo("hdhub4u.cricker", q),
        fetch_duckduckgo("kittymovies.cc", q),
        fetch_duckduckgo("1kuttymovies.cc", q)
    ]
    results = await asyncio.gather(*tasks)
    return JSONResponse({
        "tmdb": tmdb_data,
        "filmxy": results[0],
        "hdhub4u": results[1],
        "kittymovies": results[2],
        "kuttymovies": results[3]
    })

@app.get("/show")
async def show_downloads(q: str = Query(...)):
    tmdb_data = await fetch_tmdb(q)
    tasks = [
        fetch_duckduckgo("filmxy.vip", q),
        fetch_duckduckgo("hdhub4u.cricker", q),
        fetch_duckduckgo("kittymovies.cc", q),
        fetch_duckduckgo("1kuttymovies.cc", q)
    ]
    results = await asyncio.gather(*tasks)
    all_links = results[0] + results[1] + results[2] + results[3]
    return JSONResponse({
        "tmdb": tmdb_data,
        "downloads": all_links
    })

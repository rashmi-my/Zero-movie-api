from fastapi import FastAPI, Query
from bs4 import BeautifulSoup
import requests
import re

app = FastAPI()

HEADERS = {"User-Agent": "Mozilla/5.0"}
TMDB_API_KEY = "3a08a646f83edac9a48438ac670a78b2"

# Extract quality
def extract_quality(text):
    match = re.search(r"(480p|720p|1080p|4K|2160p)", text, re.IGNORECASE)
    return match.group(1) if match else "Unknown"

# Extract language
def extract_language(text):
    langs = ["Tamil", "Hindi", "English", "Telugu", "Malayalam", "Kannada", "Dual Audio"]
    for lang in langs:
        if lang.lower() in text.lower():
            return lang
    return "Unknown"

# TMDB Search
def get_tmdb_data(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    res = requests.get(url)
    if res.status_code != 200 or not res.json().get("results"):
        return {}
    movie = res.json()["results"][0]
    return {
        "title": movie.get("title"),
        "year": movie.get("release_date", "")[:4],
        "rating": movie.get("vote_average"),
        "overview": movie.get("overview"),
        "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else "",
        "tmdb_link": f"https://www.themoviedb.org/movie/{movie.get('id')}"
    }

# DuckDuckGo Scraper
def duck_search(site, query):
    url = f"https://duckduckgo.com/html?q=site:{site} {query} movie download"
    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for link in soup.select(".result__a")[:3]:
        results.append({"title": link.text, "link": link['href']})
    return results

@app.get("/")
def root():
    return {"message": "Welcome to Zero Super Movie API with Quality & Language!"}

@app.get("/search")
def search_all(q: str = Query(..., description="Movie name")):
    return {
        "tmdb": get_tmdb_data(q),
        "filmxy": duck_search("filmxy.vip", q),
        "hdhub4u": duck_search("hdhub4u.cricker", q),
        "kittymovies": duck_search("kittymovies.cc", q)
    }

@app.get("/show")
def show_links(q: str = Query(..., description="Movie name to get download links")):
    data = {
        "filmxy": [],
        "hdhub4u": [],
        "kittymovies": []
    }

    # Filmxy
    for result in duck_search("filmxy.vip", q):
        try:
            r = requests.get(result["link"], headers=HEADERS, timeout=10)
            s = BeautifulSoup(r.text, "html.parser")
            links = s.select("a[href*='filmxy.vip/download/']")
            data["filmxy"].append({
                "title": result["title"],
                "link": result["link"],
                "downloads": [{
                    "url": l["href"],
                    "quality": extract_quality(l.text),
                    "language": extract_language(l.text)
                } for l in links]
            })
        except:
            continue

    # HDHub4u
    for result in duck_search("hdhub4u.cricker", q):
        try:
            r = requests.get(result["link"], headers=HEADERS, timeout=10)
            s = BeautifulSoup(r.text, "html.parser")
            links = s.select("a[href*='download']")
            data["hdhub4u"].append({
                "title": result["title"],
                "link": result["link"],
                "downloads": [{
                    "url": l["href"],
                    "quality": extract_quality(l.text),
                    "language": extract_language(l.text)
                } for l in links]
            })
        except:
            continue

    # KittyMovies
    for result in duck_search("kittymovies.cc", q):
        try:
            r = requests.get(result["link"], headers=HEADERS, timeout=10)
            s = BeautifulSoup(r.text, "html.parser")
            links = s.select("a[href$='.mkv'], a[href$='.mp4'], a[href*='download']")
            data["kittymovies"].append({
                "title": result["title"],
                "link": result["link"],
                "downloads": [{
                    "url": l["href"],
                    "quality": extract_quality(l.text),
                    "language": extract_language(l.text)
                } for l in links]
            })
        except:
            continue

    return {
        "tmdb": get_tmdb_data(q),
        "downloads": data
    }

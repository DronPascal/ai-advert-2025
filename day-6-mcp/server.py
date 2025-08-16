import os
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from readability import Document

app = FastAPI()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    enrich: bool = False


@app.get("/healthz")
async def healthz():
    return {"ok": True}


@app.get("/tools")
async def tools():
    return {"tools": [{"name": "web.search"}]}


@app.post("/search")
async def search(req: SearchRequest):
    query = req.query.strip()
    top_k = max(1, min(10, req.top_k))

    brave_key = os.getenv("BRAVE_API_KEY")
    serp_key = os.getenv("SERPAPI_KEY")

    results = []

    if brave_key:
        # Brave Search API
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"Accept": "application/json", "X-Subscription-Token": brave_key}
        params = {"q": query, "count": top_k}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 200:
                data = r.json()
                web = data.get("web", {}).get("results", [])
                for item in web[:top_k]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", "")
                    })
    elif serp_key:
        # SerpAPI Google
        url = "https://serpapi.com/search.json"
        params = {"engine": "google", "q": query, "num": top_k, "api_key": serp_key}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("organic_results", [])[:top_k]:
                    results.append({
                        "title": item.get("title", ""),
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", "")
                    })
    else:
        # Wikipedia API (language-aware). Prefer RU for Cyrillic queries, else EN.
        def contains_cyrillic(text: str) -> bool:
            return any('А' <= ch <= 'я' or ch == 'ё' or ch == 'Ё' for ch in text)

        async def wiki_search(lang: str) -> list[dict]:
            host = f"https://{lang}.wikipedia.org"
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.get(
                    f"{host}/w/api.php",
                    params={
                        "action": "query",
                        "list": "search",
                        "srsearch": query,
                        "utf8": 1,
                        "format": "json",
                        "srlimit": top_k,
                    },
                    headers={"User-Agent": "mcp-web-gateway/1.0", "Accept-Language": lang}
                )
                out: list[dict] = []
                if r.status_code == 200:
                    data = r.json()
                    for s in data.get("query", {}).get("search", [])[:top_k]:
                        title = s.get("title", "")
                        page_url = f"{host}/wiki/{title.replace(' ', '_')}"
                        snippet = s.get("snippet", "").replace("<span class=\"searchmatch\">", "").replace("</span>", "")
                        out.append({"title": title, "url": page_url, "snippet": snippet})
                return out

        try:
            preferred = "ru" if contains_cyrillic(query) else "en"
            alt = "en" if preferred == "ru" else "ru"
            items = await wiki_search(preferred)
            if not items:
                items = await wiki_search(alt)
            results.extend(items)
        except Exception:
            pass

    if req.enrich and results:
        # choose first valid content page (filter SERP/aggregators)
        SERP_HOST_PARTS = [
            "duckduckgo.com", "google.", "bing.com", "yandex.", "search.yahoo.",
            "/search?", "/search/", "news.yandex", "go.mail.ru/search"
        ]
        def is_valid(url: str) -> bool:
            if not url:
                return False
            low = url.lower()
            return not any(part in low for part in SERP_HOST_PARTS)

        pick_idx = 0
        for i, item in enumerate(results):
            if is_valid(item.get("url", "")):
                pick_idx = i
                break

        picked_url = results[pick_idx].get("url")
        if picked_url:
            try:
                async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                    r = await client.get(picked_url, headers={"User-Agent": "mcp-web-gateway/1.0"})
                    if r.status_code == 200 and r.headers.get("content-type", "").startswith("text/html"):
                        # Try readability first
                        try:
                            doc = Document(r.text)
                            html = doc.summary(html_partial=True)
                            soup = BeautifulSoup(html, "lxml")
                            text = soup.get_text("\n", strip=True)
                        except Exception:
                            soup = BeautifulSoup(r.text, "lxml")
                            paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
                            text = "\n\n".join(p for p in paragraphs if p)
                        if text:
                            results[pick_idx]["content"] = text[:16000]
                            results[pick_idx]["picked_url"] = str(r.url)
            except Exception:
                pass

    return {"results": results[:top_k]}




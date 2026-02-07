import asyncio
import json
import re
import time
from datetime import datetime
from typing import List, Dict

import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

DATE_RANGE = "d"


async def async_fetch_url(
    client: httpx.AsyncClient,
    url: str,
    timeout: float = 12.0
) -> str | None:
    try:
        resp = await client.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return None


def extract_relevant_text(html: str | None, keyword: str) -> str:
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Remove noise
    for tag in soup(["script", "style", "header", "footer", "nav", "aside", "form", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s{2,}", " ", text).strip()

    if not text:
        return ""

    # Find sentences containing the keyword
    sentences = re.split(r"[.!?]\s+", text)
    relevant = [s.strip() for s in sentences if keyword.lower() in s.lower()]

    if not relevant:
        return ""

    return " ".join(relevant[:7])  # limit per page


async def scrape_one(
    client: httpx.AsyncClient,
    url: str,
    keyword: str,
    semaphore: asyncio.Semaphore,
    sid: str
) -> Dict[str, str] | None:
    async with semaphore:
        html = await async_fetch_url(client, url)
        if not html:
            return None

        info = extract_relevant_text(html, keyword)
        if not info:
            return None

        result = {
            "url": url,
            "content": info
        }
        
        # Emit result immediately via WebSocket
        socketio.emit('scrape_result', result, room=sid)
        
        return result


async def scrape_all(urls: List[str], keyword: str, sid: str, max_concurrent: int = 28):
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(
        http2=True,
        headers=headers,
        follow_redirects=True,
        timeout=15.0
    ) as client:
        tasks = [
            scrape_one(client, url, keyword, semaphore, sid)
            for url in urls
        ]

        completed = 0
        for coro in asyncio.as_completed(tasks):
            result = await coro
            if result:
                results.append(result)
            
            completed += 1
            # Emit progress update
            socketio.emit('scrape_progress', {
                'completed': completed,
                'total': len(urls)
            }, room=sid)

    return results


@socketio.on('start_scrape')
def handle_scrape(data):
    keyword = data.get('keyword', '').strip()
    date_range = data.get('date_range', 'd')
    
    if not keyword:
        emit('scrape_error', {'message': 'Keyword is required'})
        return
    
    sid = request.sid
    
    # Update global DATE_RANGE
    global DATE_RANGE
    DATE_RANGE = date_range
    
    start_time = time.time()
    
    # Emit search started
    socketio.emit('scrape_started', {
        'keyword': keyword,
        'date_range': date_range
    }, room=sid)
    
    result_urls = []
    
    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query=keyword,
                region="in-en",
                safesearch="off",
                timelimit=date_range,
                max_results=50,
            )
            for res in results:
                url = res.get("href") or res.get("url")
                if url and url.startswith(("http://", "https://")):
                    result_urls.append(url)
    except Exception as e:
        emit('scrape_error', {'message': f'Search error: {str(e)}'})
        return
    
    # Emit URLs found
    socketio.emit('urls_found', {
        'count': len(result_urls)
    }, room=sid)
    
    if not result_urls:
        emit('scrape_complete', {
            'keyword': keyword,
            'total_urls_found': 0,
            'successful_scrapes': 0,
            'elapsed_time_seconds': 0
        })
        return
    
    # Run the async scraper
    all_snippets = asyncio.run(scrape_all(result_urls, keyword, sid, max_concurrent=28))
    
    elapsed_time = time.time() - start_time
    
    # Prepare final data
    output_data = {
        "keyword": keyword,
        "date_range": date_range,
        "timestamp": datetime.now().isoformat(),
        "total_urls_found": len(result_urls),
        "successful_scrapes": len(all_snippets),
        "elapsed_time_seconds": round(elapsed_time, 2),
        "results": all_snippets
    }
    
    # Save to JSON file
    filename = f"scrape_{keyword.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Emit completion
    socketio.emit('scrape_complete', {
        'keyword': keyword,
        'total_urls_found': len(result_urls),
        'successful_scrapes': len(all_snippets),
        'elapsed_time_seconds': round(elapsed_time, 2),
        'filename': filename
    }, room=sid)


@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == '__main__':
    print("🚀 WebSocket Scraper Server starting...")
    print("📡 Server running on http://localhost:5000")
    print("🔌 WebSocket endpoint: ws://localhost:5000/socket.io/")
    print("\n✨ Open http://localhost:5000 in your browser to use the scraper\n")
    socketio.run(app, debug=False, host='0.0.0.0', port=5000, use_reloader=False, log_output=False)

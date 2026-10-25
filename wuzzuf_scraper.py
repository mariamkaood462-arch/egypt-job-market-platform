import json
import sys
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://wuzzuf.net"
SEARCH = BASE + "/search/jobs/"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def fetch(query, page):
    r = requests.get(SEARCH, params={"q": query, "start": page}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def save_raw(html, query, page):
    folder = Path("data/bronze/wuzzuf") / str(date.today())
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{query.replace(' ', '_')}_page_{page}.html").write_text(html, encoding="utf-8")


def parse_page(html, query):
    soup = BeautifulSoup(html, "html.parser")
    jobs, seen = [], set()
    for link in soup.select('a[href*="/jobs/p/"]'):
        url = BASE + link["href"] if link["href"].startswith("/") else link["href"]
        title = link.get_text(strip=True)
        if not title or url in seen:
            continue
        seen.add(url)
        card = link
        for _ in range(6):
            card = card.parent
            if card is None or card.select_one('a[href*="/jobs/careers/"]'):
                break
        if card is None:
            continue
        company = card.select_one('a[href*="/jobs/careers/"]')
        skills = [a.get_text(strip=True) for a in card.select('a[href*="/a/"]')]
        jobs.append({
            "source": "wuzzuf",
            "query": query,
            "scraped_date": str(date.today()),
            "title": title,
            "url": url,
            "company": company.get_text(strip=True) if company else None,
            "skills": skills,
            "card_text": card.get_text(" | ", strip=True),
        })
    return jobs


def main(query, pages):
    out_dir = Path("data/silver_raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"wuzzuf_{date.today()}.jsonl"
    total = 0
    with out_file.open("a", encoding="utf-8") as f:
        for page in range(pages):
            try:
                html = fetch(query, page)
            except requests.RequestException as e:
                print(f"page {page}: failed ({e})")
                continue
            save_raw(html, query, page)
            jobs = parse_page(html, query)
            for job in jobs:
                f.write(json.dumps(job, ensure_ascii=False) + "\n")
            total += len(jobs)
            print(f"page {page}: {len(jobs)} jobs")
            if not jobs:
                break
            time.sleep(3)
    print(f"done: {total} jobs -> {out_file}")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "data engineer"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    main(q, n)
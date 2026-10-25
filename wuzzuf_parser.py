import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = "https://wuzzuf.net"


def parse_page(html, query="", scraped_date=""):
    soup = BeautifulSoup(html, "html.parser")
    jobs, seen = [], set()
    for link in soup.select('a[href*="/jobs/p/"]'):
        href = link["href"]
        url = BASE + href if href.startswith("/") else href
        title = link.get_text(strip=True)
        if not title or url in seen:
            continue
        seen.add(url)

        # اطلعي لفوق لحد آخر عنصر فيه وظيفة واحدة بس
        card = link
        while card.parent is not None:
            urls = {a["href"].split("?")[0] for a in card.parent.select('a[href*="/jobs/p/"]')}
            if len(urls) > 1:
                break
            card = card.parent

        company = card.select_one('a[href*="/jobs/careers/"]')
        strings = list(card.stripped_strings)

        tags = []
        for i, s in enumerate(strings):
            if s == "·" and i + 1 < len(strings):
                tags.append(strings[i + 1])
            elif s.startswith("· ") and len(s) > 2:
                tags.append(s[2:].strip())

        jobs.append({
            "source": "wuzzuf",
            "query": query,
            "scraped_date": scraped_date,
            "title": title,
            "url": url,
            "company": company.get_text(strip=True) if company else None,
            "tags": tags,
            "card_text": " | ".join(strings),
        })
    return jobs


if __name__ == "__main__":
    out = Path("data/silver_raw/wuzzuf_reparsed.jsonl")
    all_jobs, seen_urls = [], set()
    for f in sorted(Path("data/bronze/wuzzuf").glob("*/*.html")):
        query = f.stem.rsplit("_page_", 1)[0].replace("_", " ")
        for job in parse_page(f.read_text(encoding="utf-8"), query, f.parent.name):
            if job["url"] not in seen_urls:
                seen_urls.add(job["url"])
                all_jobs.append(job)
    with out.open("w", encoding="utf-8") as fh:
        for job in all_jobs:
            fh.write(json.dumps(job, ensure_ascii=False) + "\n")
    print("jobs:", len(all_jobs))
    print("jobs with tags:", sum(1 for j in all_jobs if j["tags"]))
    print("longest card_text:", max(len(j["card_text"]) for j in all_jobs))
    print(json.dumps(all_jobs[1], ensure_ascii=False, indent=2))
import json
import sys
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from wuzzuf_scraper import parse_page, save_raw

query = sys.argv[1] if len(sys.argv) > 1 else "data engineer"
pages = int(sys.argv[2]) if len(sys.argv) > 2 else 2

out_dir = Path("data/silver_raw")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / f"wuzzuf_{date.today()}.jsonl"

total = 0
with sync_playwright() as p:
    # profile بيتحفظ فيه الجلسة بعد ما تعدّي التحقق
    context = p.chromium.launch_persistent_context("pw_profile", headless=False)
    page = context.new_page()
    with out_file.open("a", encoding="utf-8") as f:
        for n in range(pages):
            url = f"https://wuzzuf.net/search/jobs/?q={query.replace(' ', '+')}&start={n}"
            page.goto(url, wait_until="domcontentloaded")

            # استني لحد 90 ثانية لحد ما صفحة التحقق تختفي
            for _ in range(45):
                if "Just a moment" not in page.title():
                    break
                if _ == 0:
                    print(">>> لو ظهر مربع تحقق في Chrome اضغطي عليه بإيدك...")
                page.wait_for_timeout(2000)

            page.wait_for_timeout(3000)
            html = page.content()
            save_raw(html, query, n)
            jobs = parse_page(html, query)
            for job in jobs:
                f.write(json.dumps(job, ensure_ascii=False) + "\n")
            total += len(jobs)
            print(f"page {n}: {len(jobs)} jobs | title: {page.title()}")
            if not jobs:
                break
    context.close()

print(f"done: {total} jobs -> {out_file}")
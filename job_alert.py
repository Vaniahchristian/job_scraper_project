#!/usr/bin/env python3
"""
Daily job alert scraper for Uganda tech job boards.

What this does:
- Pulls new job listings from a few Uganda job sites that publish public RSS
  feeds (meant for exactly this kind of automated use, so no robots.txt or
  terms-of-service issue).
- Filters listings against a keyword list built from your skills
  (React, Node, Flutter, Laravel, full-stack, etc).
- Keeps track of what it has already alerted you about (seen_jobs.json) so
  you never get the same listing twice.
- Sends new matches to you on Telegram.

What this deliberately does NOT do:
- Scrape LinkedIn. LinkedIn requires login and its Terms of Service forbid
  automated scraping. Use LinkedIn's own "Create search alert" feature
  instead (see README.md for the two-minute setup).
- Scrape BrighterMonday directly. Their robots.txt disallows automated
  access. Use their built-in "Job Alerts" email subscription instead
  (see README.md).
"""

import json
import os
import re
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import xml.etree.ElementTree as ET

STATE_FILE = Path(__file__).parent / "seen_jobs.json"

# Keywords matched against job title + summary, case-insensitive.
# Edit this list any time your target roles change.
KEYWORDS = [
    "software developer", "software engineer", "web developer",
    "full stack", "full-stack", "backend developer", "back-end developer",
    "frontend developer", "front-end developer", "mobile developer",
    "flutter developer", "react developer", "react native",
    "node.js developer", "nodejs developer", "laravel developer",
    "php developer", ".net developer", "dotnet developer",
    "javascript developer", "typescript developer", "api developer",
    "devops", "cloud engineer", "systems developer", "applications developer",
    "programmer", "it developer", "web development", "software development",
]

# Sources: each is a public RSS/Atom feed. Add more here as you find them.
SOURCES = {
    "The Ugandan Jobline": "https://theugandanjobline.com/feeds/posts/default?alt=rss",
    "Daily Job Net": "https://dailyjobnet.com/feed/",
}

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def load_seen():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen):
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=2))


def fetch(url, timeout=20):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (job-alert-script)"})
    with urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_rss(xml_bytes):
    """Returns list of (title, link, summary) tuples from an RSS/Atom feed."""
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return items

    # Standard RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        if title and link:
            items.append((title, link, desc))

    # Atom fallback
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//a:entry", ns):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
            link_el = entry.find("a:link", ns)
            link = link_el.get("href") if link_el is not None else ""
            summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
            if title and link:
                items.append((title, link, summary))

    return items


def matches_keywords(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw in text for kw in KEYWORDS)


def clean_html(text):
    return re.sub("<[^<]+?>", "", text).strip()


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        print("Would have sent:\n", message)
        return
    import urllib.parse
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }).encode()
    req = Request(url, data=data)
    try:
        with urlopen(req, timeout=20) as resp:
            resp.read()
    except URLError as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)


def main():
    seen = load_seen()
    new_matches = []

    for source_name, feed_url in SOURCES.items():
        try:
            raw = fetch(feed_url)
        except Exception as e:
            print(f"[{source_name}] fetch failed: {e}", file=sys.stderr)
            continue

        for title, link, summary in parse_rss(raw):
            if link in seen:
                continue
            summary_clean = clean_html(summary)
            if matches_keywords(title, summary_clean):
                new_matches.append((source_name, title, link))
            seen.add(link)  # mark seen either way so we don't re-check non-matches forever

    if new_matches:
        lines = [f"<b>{len(new_matches)} new job match(es) today</b>\n"]
        for source_name, title, link in new_matches:
            lines.append(f"\u2022 <b>{title}</b>\n  {source_name}\n  {link}")
        message = "\n\n".join(lines)
        # Telegram messages cap at 4096 chars; split if needed
        for i in range(0, len(message), 3500):
            send_telegram(message[i:i + 3500])
        print(f"Sent {len(new_matches)} new matches.")
    else:
        print("No new matches today.")

    save_seen(seen)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Daily job alert scraper for Uganda tech job boards.

What this does:
- Pulls new job listings from Uganda / East Africa job sites that publish
  public RSS feeds (meant for exactly this kind of automated use, so no
  robots.txt or terms-of-service issue).
- Filters listings against a keyword list built from your skills
  (React, Node, Flutter, Laravel, full-stack, etc).
- Keeps track of what it has already alerted you about (seen_jobs.json) so
  you never get the same listing twice.
- Sends new matches to you on Telegram.

Coverage map (scraped vs official alerts):
- Scraped via RSS: The Ugandan Jobline, Daily Job Net, JobAdverts.ug, ReliefWeb Uganda
  (NGO / humanitarian — stands in for UNjobs), Q-Sourcing Servtec
  (engineering / energy).
- Official alerts only (see README.md): BrighterMonday, Fuzu, LinkedIn,
  Great Uganda Jobs. Those either block bots or have no public feed.

What this deliberately does NOT do:
- Scrape LinkedIn. LinkedIn requires login and its Terms of Service forbid
  automated scraping. Use LinkedIn's own "Create search alert" feature
  instead (see README.md for the two-minute setup).
- Scrape BrighterMonday, Fuzu, or Great Uganda Jobs. No usable public RSS
  (and BrighterMonday's robots.txt disallows automated access). Use each
  site's built-in job-alert email / account alerts instead (see README.md).
"""

import json
import re
import os
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
    "information technology", "information management", "data engineer", "data analyst",
    "ict", "mis officer", "database admin", "database administrator",
    "database developer", "network engineer",
]

# Sources: each is a public RSS/Atom feed. Add more here as you find them.
# Notes in comments match the board's usual strength.
SOURCES = {
    # General Uganda tech / corporate listings
    "The Ugandan Jobline": "https://theugandanjobline.com/feeds/posts/default?alt=rss",
    "Daily Job Net": "https://dailyjobnet.com/feed/",
    # Government / university / corporate round-up posts (e.g. UNCST, Makerere)
    "JobAdverts.ug": "https://jobadverts.ug/feed/",
    # NGO / humanitarian (public ReliefWeb feed — closest RSS stand-in for UNjobs Uganda)
    "ReliefWeb Uganda": "https://reliefweb.int/jobs/rss.xml?country=240",
    # Engineering / energy / technical roles across Q-Sourcing (Uganda search)
    "Q-Sourcing Servtec": "https://qsourcing.com/feed/?post_type=job_listing&s=uganda",
}

# Optional extra text that must appear in title+summary for a source.
# Used when a feed is regional and we only want Uganda hits.
SOURCE_MUST_MATCH = {
    "Q-Sourcing Servtec": (
        "uganda", "kampala", "entebbe", "gulu", "mbarara", "jinja",
        "mbale", "qssu",
    ),
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
    for kw in KEYWORDS:
        # Short tokens (e.g. "ict") must be whole words — otherwise
        # "ict" matches inside "district", "strict", org names like "ICTJ", etc.
        if len(kw) <= 3:
            if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text):
                return True
        elif kw in text:
            return True
    return False


def matches_source_location(source_name, title, summary):
    """If a source has a location allow-list, require at least one hit."""
    needles = SOURCE_MUST_MATCH.get(source_name)
    if not needles:
        return True
    text = f"{title} {summary}".lower()
    return any(n in text for n in needles)


def clean_html(text):
    return re.sub("<[^<]+?>", "", text).strip()


def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured (missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        print("Would have sent:\n", message)
        return False
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
            body = json.loads(resp.read().decode())
        if not body.get("ok"):
            print(f"Telegram API error: {body}", file=sys.stderr)
            return False
        print("Telegram message sent.")
        return True
    except URLError as e:
        print(f"Failed to send Telegram message: {e}", file=sys.stderr)
        return False


def telegram_status():
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        masked = f"...{TELEGRAM_CHAT_ID[-4:]}" if len(TELEGRAM_CHAT_ID) >= 4 else "(set)"
        return f"configured (chat_id {masked})"
    return "NOT configured — check TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID secrets"


def send_test_message():
    print(f"Telegram: {telegram_status()}")
    ok = send_telegram(
        "<b>Job alert bot test</b>\n\n"
        "If you see this, Telegram is wired up correctly."
    )
    sys.exit(0 if ok else 1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        send_test_message()

    seen = load_seen()
    new_matches = []
    new_urls = 0

    print(f"Telegram: {telegram_status()}")
    print(f"Already tracking {len(seen)} job URL(s).")

    for source_name, feed_url in SOURCES.items():
        try:
            raw = fetch(feed_url)
        except Exception as e:
            print(f"[{source_name}] fetch failed: {e}", file=sys.stderr)
            continue

        items = parse_rss(raw)
        print(f"[{source_name}] {len(items)} listing(s) in feed.")

        for title, link, summary in items:
            if link in seen:
                continue
            new_urls += 1
            summary_clean = clean_html(summary)
            if (matches_source_location(source_name, title, summary_clean)
                    and matches_keywords(title, summary_clean)):
                new_matches.append((source_name, title, link))
            seen.add(link)  # mark seen either way so we don't re-check non-matches forever

    print(f"New URLs since last run: {new_urls}")
    print(f"New keyword matches: {len(new_matches)}")

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
        print("No new matches today — no Telegram message sent.")
        print("(This is normal if you already ran locally or all new listings "
              "didn't match your keywords.)")

    save_seen(seen)


if __name__ == "__main__":
    main()

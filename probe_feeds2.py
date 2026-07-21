from urllib.request import urlopen, Request
import re

def get(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (job-alert-script)"})
    with urlopen(req, timeout=20) as r:
        return r.status, r.headers.get("Content-Type",""), r.read()

# Inspect Great Uganda Jobs RSS page for real feed URLs
status, ctype, data = get("https://www.greatugandajobs.com/rss")
text = data.decode("utf-8", errors="replace")
print("=== Great Uganda Jobs /rss ===")
print("ctype:", ctype, "len:", len(data))
# find feed-like links
for m in re.findall(r'href=["\']([^"\']+)["\']', text):
    if any(x in m.lower() for x in ["rss", "feed", "atom", "xml", "feedburner"]):
        print(" link:", m)
# also look for http://http// typo mentioned in search
for m in re.findall(r'https?://[^\s<>"\']+', text):
    if any(x in m.lower() for x in ["rss", "feed", "atom", "xml", "feedburner", "great"]):
        print(" url:", m)

print("\n=== Q-Sourcing Uganda sample items ===")
status, ctype, data = get("https://qsourcing.com/jobs-in-uganda/feed/")
print("ctype:", ctype)
# count items
print("item count:", data.count(b"<item>"))
print(data[:800].decode("utf-8", errors="replace"))

print("\n=== UNDP rss variants ===")
undp_urls = [
  "https://jobs.undp.org/cj_rss_feed.cfm?iso3=UGA",
  "https://jobs.undp.org/cj_rss_feed.cfm?c=UGA",
  "https://jobs.undp.org/rss_feed.cfm?CountryID=220",
  "https://jobs.undp.org/cj_rss_feed.cfm?country=Uganda",
]
for u in undp_urls:
    try:
        status, ctype, data = get(u)
        print(f"OK {u}: ctype={ctype} start={data[:120]!r}")
    except Exception as e:
        print(f"FAIL {u}: {e}")

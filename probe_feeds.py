from urllib.request import urlopen, Request

urls = {
  "Great Uganda Jobs": "https://www.greatugandajobs.com/rss/10-all-jobs",
  "Great Uganda Jobs feedburner": "http://feeds.feedburner.com/allgreatjobs",
  "UNDP Uganda": "https://jobs.undp.org/cj_rss_feed.cfm?Country=UGA",
  "UNjobs Uganda xml": "https://unjobs.org/rss/duty_stations/uganda.xml",
  "UNjobs Uganda rss": "https://unjobs.org/duty_stations/uganda.rss",
  "UNjobs feed": "https://unjobs.org/rss",
  "Q-Sourcing feed": "https://qsourcing.com/jobs/feed/",
  "Q-Sourcing uganda feed": "https://qsourcing.com/jobs-in-uganda/feed/",
  "Fuzu feed": "https://www.fuzu.com/uganda/job/feed",
  "BrighterMonday feed": "https://www.brightermonday.co.ug/jobs/feed",
}

for name, url in urls.items():
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (job-alert-script)"})
        with urlopen(req, timeout=15) as r:
            data = r.read(300)
            ctype = r.headers.get("Content-Type", "")
            print(f"OK {name}: status={r.status} ctype={ctype}")
            print(f"  start={data[:160]!r}")
    except Exception as e:
        print(f"FAIL {name}: {type(e).__name__}: {e}")

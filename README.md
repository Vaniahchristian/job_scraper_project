# Daily Job Alert Scraper

Checks a few Uganda job boards every day and messages you on Telegram when a
new listing matches your skills. Runs for free on GitHub Actions — no
server, no laptop that has to stay on.

## What it covers, and what it doesn't

**Scrapes directly (via their public RSS feeds):**
- The Ugandan Jobline — general Uganda listings
- Daily Job Net — general Uganda listings
- JobAdverts.ug — government / university / corporate round-up posts
- ReliefWeb Uganda — NGO / humanitarian roles (public RSS stand-in for UNjobs)
- Q-Sourcing Servtec — engineering / energy / technical roles (Uganda-filtered)

**Does NOT scrape (use each site's own alerts — see below):**
- **BrighterMonday** — best for wide corporate variety; robots.txt blocks bots
- **Fuzu** — best for career guidance and entry-level; no public RSS
- **LinkedIn** — best for executive / corporate networking; ToS forbids scraping
- **Great Uganda Jobs** — best for local government / public roles; no usable RSS
- **UNjobs.org** — no public RSS; ReliefWeb Uganda above covers the same niche

This keeps the setup on the right side of every site's rules, while still
covering the non-RSS boards through their own official alert tools.

---

## Setup (about 15 minutes total)

### 1. Create a Telegram bot (free, 2 minutes)

1. In Telegram, message **@BotFather**.
2. Send `/newbot`, give it a name (e.g. "Uganda Job Alerts").
3. BotFather gives you a **bot token** — looks like `123456:ABC-defGhIjk...`.
   Save it.
4. Message your new bot anything (e.g. "hi") to start a chat with it.
5. Visit this URL in your browser (replace `<TOKEN>`):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
   Find `"chat":{"id":123456789` in the response — that number is your
   **chat ID**. Save it.

### 2. Put this code on GitHub

1. Create a new **private** GitHub repository (private so your scraper
   internals aren't public — the code itself has nothing secret in it, but
   no reason to make it public).
2. Upload all the files in this folder to the repo (or `git push` them).

### 3. Add your secrets

In the repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add two secrets:
- `TELEGRAM_BOT_TOKEN` → the token from step 1
- `TELEGRAM_CHAT_ID` → the chat ID from step 1

### 4. Turn it on

The workflow in `.github/workflows/daily.yml` runs automatically three times
a day at 06:00, 12:00, and 18:00 East Africa Time. You can also trigger it
manually any time from the repo's **Actions** tab → "Daily Job Alert" →
"Run workflow", to test it immediately instead of waiting for the schedule.

That's it. New matching jobs will land in your Telegram chat every day.

---

## Covering LinkedIn (official, free, 2 minutes)

1. On LinkedIn, search for e.g. "Software Engineer" with location "Kampala,
   Uganda" (or "Uganda" / "Remote").
2. Above the results, toggle **"Set alert"**.
3. Choose **daily** frequency, and whether you want it by email or LinkedIn
   notification (push notification works well if you have the app).

Repeat for a couple of different searches (e.g. "Full Stack Developer",
"React Developer") to widen coverage — LinkedIn lets you keep several alerts
active at once.

## Covering BrighterMonday (official, free, 2 minutes)

1. Go to brightermonday.co.ug, search "IT & Software" jobs.
2. Look for **"Sign up for job alerts"** on the results page, enter your
   email, and select the IT & Software category.

## Covering Fuzu (official, free)

1. Create a free account at [fuzu.com/uganda](https://www.fuzu.com/uganda).
2. Set location to Uganda and turn on **smart job alerts** for the roles
   you want (entry-level and career-guidance listings are Fuzu's strength).

## Covering Great Uganda Jobs (official, free)

1. Open [greatugandajobs.com/jobseeker/job-alerts](https://www.greatugandajobs.com/jobseeker/job-alerts).
2. Subscribe with your email — useful for local government and public-sector
   roles that rarely show up on the tech boards.

## Covering UNjobs / NGO roles

ReliefWeb Uganda is already scraped by this script (NGO / humanitarian).
Optionally also bookmark [unjobs.org/duty_stations/uganda](https://unjobs.org/duty_stations/uganda)
and check it weekly for agency postings that aren't on ReliefWeb yet.

---

## Tuning it

- **Keywords:** edit the `KEYWORDS` list near the top of `job_alert.py` to
  add or remove terms.
- **More sources:** add more entries to the `SOURCES` dict — any site with
  a public RSS/Atom feed works. Look for a `/feed/` or `/feeds/posts/default`
  URL on the site, or check their homepage footer for an RSS icon.
- **Schedule:** edit the `cron` line in `.github/workflows/daily.yml` if you
  want it to run at a different time or more than once a day.

## Running it locally instead (optional)

```bash
export TELEGRAM_BOT_TOKEN="your-token"
export TELEGRAM_CHAT_ID="your-chat-id"
python3 job_alert.py
```

No extra packages needed — it only uses Python's standard library.

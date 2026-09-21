# AUDIT — WebScraping-Mars (pre-refactor)

Audit of the previous build: `scrape_mars.py` (313 lines driving a
headless browser with Splinter), `app.py` (Flask over MongoDB), a
template, three images. To see the dashboard you needed Chrome,
chromedriver, MongoDB and a running Flask process; nothing was
deployed.

---

## A. What no longer worked

### A1 — All four target sites are gone
`redplanetscience.com`, `spaceimages-mars.com`, `galaxyfacts-mars.com`
and `marshemispheres.com` (lines 117, 162, 202, 244) no longer resolve.
Every scraper function fell through to a `via.placeholder.com` image or
an empty table, silently. **Fix:** the two static mirrors the exercise
now uses (news and Curiosity REMS weather) are the sources; a fetch
failure is an error, and the report says which snapshot it rendered.

### A2 — Browser automation for static pages
Splinter + chromedriver to fetch HTML that `requests` returns in one
call. **Fix:** `requests` with a timeout and a named user agent;
parsers are pure functions over HTML, tested on committed fixtures.

### A3 — MongoDB and Flask to show one page
`app.py` wrote the scrape into Mongo and served a template from it.
**Fix:** a scheduled GitHub Action writes `data/snapshot.json` and the
CI pipeline renders a static dashboard to Pages. No database, no
server.

## B. Correctness

### B1 — Failures hidden behind placeholders
Lines 191 and 304 returned placeholder image URLs when a scrape failed,
so the page always looked complete. **Fix:** parsers raise on a changed
structure; the live build falls back to the committed snapshot and
states so on the page.

### B2 — No analysis of the data it scraped
The weather table was displayed as HTML and never computed on. **Fix:**
`weather.py` computes mean minimum temperature and pressure by Martian
month, the coldest, warmest, lowest- and highest-pressure months, and
the length of the Martian year from the spacing of Ls = 0 crossings —
687.0 Earth days against the accepted 686.98.

## C. Engineering

### C1 — No tests, no CI
**Fix:** 7 pytest tests at 99 % statement coverage: both parsers on
fixtures with five structural rejections, the classic weather answers
(months 3, 8, 6, 9), the year estimate within a day, the fallback
estimator, snapshot and report writing, and `fetch` error handling;
ruff, mypy strict, bandit, pip-audit, Trivy.

### C2 — Stock images
**Fix:** removed; one current screenshot in `docs/`.

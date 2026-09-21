# Case Study — WebScraping-Mars

**Repository:** [WebScraping-Mars](https://github.com/Freddricklogan/WebScraping-Mars) · **Live dashboard:** [freddricklogan.github.io/WebScraping-Mars](https://freddricklogan.github.io/WebScraping-Mars/) · **Author:** Freddrick Logan

---

## 1. Who has this problem

Anyone who keeps a scraper alive: the analyst whose weekly report depends on a page that changes shape, the team that inherited a script wired to a database nobody can reach, and students who learn scraping as a one-off notebook and never see what it takes to run one on a schedule. The Mars pages are a teaching target; the operating pattern is what transfers.

## 2. The problem, as a scenario

A reviewer clones the repository. The README says to install Chrome, chromedriver, MongoDB and Flask. She does, runs the scraper, and gets a page of placeholder images: all four target sites disappeared years ago, and every function was written to substitute a placeholder rather than report a failure. The weather table, when it existed, was displayed and never computed on. Nothing was deployed, so there was nothing to check. That was the earlier version of this repository.

## 3. What it costs to leave it alone

A scraper that hides failure produces a dashboard that is always complete and sometimes wrong, which is worse than one that is visibly broken. A pipeline that needs a browser, a database and a server to render one page will not be run again after the author's laptop changes. And a portfolio piece that cannot be opened is a portfolio piece that does not exist.

## 4. The approach, and the alternative I rejected

I rejected restoring the browser-and-database architecture with new target sites; the sites were the least stable part, and the architecture was the reason nothing shipped. Instead the exercise's two static mirrors — a news page and the Curiosity REMS weather table — became the sources, fetched with `requests` and parsed by pure functions tested on committed fixtures, each of which raises with a reason when the page structure changes. A weekly GitHub Action runs the scraper and commits `data/snapshot.json` when it differs. The CI build renders the dashboard from a live scrape when the sources answer and from the committed snapshot when they do not, printing which on the page. `weather.py` computes what the exercise asks: monthly means, the coldest and warmest months, pressure extremes, and the Martian year from the spacing of Ls = 0 crossings.

## 5. What the code does today

`marsdash scrape` fetches both pages, parses them, and writes a snapshot with the fetch time and source URLs. `marsdash report --live` writes a dashboard with the Executive Shell: a provenance line saying whether this build scraped live or used the committed snapshot and when the data were fetched; bar charts of mean minimum temperature and mean pressure by Martian month with a table beneath; the coldest, warmest, lowest- and highest-pressure months with their values; the measured Martian year beside the accepted figure; and the fifteen parsed headlines with dates and teasers. The snapshot ships next to the page. The weekly refresh workflow commits a changed snapshot to the main branch, which triggers the normal build.

## 6. Evidence

Seven tests at 99 % statement coverage cover the news parser on the fixture and its empty-page rejection; the weather parser's first row field by field, the date range, and five structural rejections (wrong header, no rows, short row, month out of range, bad date); the monthly aggregation summing to 1,867 sols with the classic answers — months 3 and 8 for temperature, 6 and 9 for pressure — and the year estimate within a day of 686.98; the fallback estimator on a single year of data; snapshot and report writing with template substitution checked; bad-snapshot rejections; and `fetch` raising on an error status. The live run scraped 15 articles and 1,867 observations from 2012-08-16 to 2018-02-27 and measured a Martian year of 687.0 days. The dashboard rendered with zero console errors and no horizontal scroll at 1280 or 400 pixels. `AUDIT.md` records seven findings.

## 7. What it would take to run this in production

Point the scraper at the sources a real programme cares about, with a robots and terms review for each; keep the fixture-based parser tests and add a contract test that alerts when the live page stops matching the fixture; store snapshots with a retention rule rather than overwriting one file; and put the refresh job on the cadence the source actually changes at. The report layer would not change.

## 8. Limits and next steps

The sources are static teaching mirrors, so the weekly refresh will usually find nothing new — the mechanism is real, the churn is not. The year estimate depends on the data spanning at least two Ls = 0 crossings; the fallback is rougher. Next, in order: a diff view between consecutive snapshots, retention of historical snapshots, and a second source with genuine change to exercise the refresh path.

## 9. Who should look at this

**Hiring manager:** evidence that I turn a fragile one-off into an operable pipeline and refuse to let failure hide behind placeholders.
**Consulting client:** a template for a scheduled data feed with provenance, fallback and no infrastructure to maintain.
**Engineer:** read `src/marsdash/scrape.py` with the fixture tests for the parser contract, and `weather.py` for the year estimate.

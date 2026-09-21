"""Fetching and parsing. Parsers are pure functions over HTML so they are tested on committed
fixtures; `fetch` is the only network call and it fails loudly."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup

NEWS_URL = "https://static.bc-edx.com/data/web/mars_news/index.html"
WEATHER_URL = "https://static.bc-edx.com/data/web/mars_facts/temperature.html"
USER_AGENT = "marsdash/1.0 (+https://github.com/Freddricklogan/WebScraping-Mars)"
TIMEOUT = 30


@dataclass(frozen=True)
class Article:
    date: str  # as printed on the page, e.g. "November 9, 2022"
    title: str
    teaser: str


@dataclass(frozen=True)
class Observation:
    id: int
    terrestrial_date: str  # YYYY-MM-DD
    sol: int
    ls: int  # solar longitude, degrees
    month: int  # Martian month 1-12
    min_temp: float  # degrees Celsius
    pressure: float  # pascals


def fetch(url: str) -> str:
    """GET the page; raise on any non-200 response."""
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def parse_news(html: str) -> list[Article]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[Article] = []
    for item in soup.select("div.list_text"):
        date = item.select_one("div.list_date")
        title = item.select_one("div.content_title")
        teaser = item.select_one("div.article_teaser_body")
        if not (date and title and teaser):
            continue
        out.append(
            Article(
                date.get_text(strip=True), title.get_text(strip=True), teaser.get_text(strip=True)
            )
        )
    if not out:
        msg = "no articles found: page structure changed"
        raise ValueError(msg)
    return out


def parse_weather(html: str) -> list[Observation]:
    soup = BeautifulSoup(html, "html.parser")
    header = [th.get_text(strip=True) for th in soup.select("table tr th")]
    expected = ["id", "terrestrial_date", "sol", "ls", "month", "min_temp", "pressure"]
    if header != expected:
        msg = f"unexpected weather table header: {header}"
        raise ValueError(msg)
    rows: list[Observation] = []
    for tr in soup.select("table tr.data-row"):
        cells = [td.get_text(strip=True) for td in tr.select("td")]
        if len(cells) != 7:
            msg = f"row with {len(cells)} cells"
            raise ValueError(msg)
        rows.append(
            Observation(
                id=int(cells[0]),
                terrestrial_date=cells[1],
                sol=int(cells[2]),
                ls=int(cells[3]),
                month=int(cells[4]),
                min_temp=float(cells[5]),
                pressure=float(cells[6]),
            )
        )
    if not rows:
        msg = "no weather rows found"
        raise ValueError(msg)
    for r in rows:
        datetime.strptime(r.terrestrial_date, "%Y-%m-%d").replace(tzinfo=UTC)
        if not 1 <= r.month <= 12:
            msg = f"row {r.id}: month {r.month} out of range"
            raise ValueError(msg)
    return rows


def snapshot(news_html: str, weather_html: str, fetched_at: str | None = None) -> dict[str, object]:
    """The JSON the scheduled job writes: parsed data plus provenance."""
    return {
        "fetched_at": fetched_at or datetime.now(UTC).isoformat(timespec="seconds"),
        "sources": {"news": NEWS_URL, "weather": WEATHER_URL},
        "articles": [a.__dict__ for a in parse_news(news_html)],
        "observations": [o.__dict__ for o in parse_weather(weather_html)],
    }

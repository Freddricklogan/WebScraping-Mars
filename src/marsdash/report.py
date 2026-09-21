"""Static dashboard — the Pages artefact — rendered from a snapshot JSON (live scrape or the
committed fallback). Every figure is computed from the snapshot; the page says which it used."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from string import Template

from .scrape import Article, Observation
from .weather import MonthStat, by_month, date_range, extremes, year_length_days

PKG = Path(__file__).parent
SHELL_DIR = PKG / "shell"
TEMPLATES = PKG / "templates"


def load_snapshot(path: Path) -> dict[str, object]:
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    for key in ("fetched_at", "sources", "articles", "observations"):
        if key not in data:
            msg = f"snapshot is missing {key!r}"
            raise ValueError(msg)
    return data


def _list(data: dict[str, object], key: str) -> list[dict[str, object]]:
    raw = data[key]
    if not isinstance(raw, list):
        msg = f"snapshot {key!r} must be a list"
        raise ValueError(msg)
    return raw


def _articles(data: dict[str, object]) -> list[Article]:
    return [Article(**a) for a in _list(data, "articles")]  # type: ignore[arg-type]


def _observations(data: dict[str, object]) -> list[Observation]:
    return [Observation(**o) for o in _list(data, "observations")]  # type: ignore[arg-type]


def _row(cells: list[str], head: bool = False) -> str:
    tag = "th" if head else "td"
    return "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"


def _news_list(articles: list[Article]) -> str:
    items = "".join(
        f"<li><strong>{html.escape(a.title)}</strong> "
        f'<span class="md-date">{html.escape(a.date)}</span><br>{html.escape(a.teaser)}</li>'
        for a in articles
    )
    return f'<ol class="md-news">{items}</ol>'


def _month_table(stats: list[MonthStat]) -> str:
    rows = [
        _row(
            ["Martian month", "Sols observed", "Mean minimum temp (°C)", "Mean pressure (Pa)"],
            head=True,
        )
    ]
    rows += [
        _row([str(s.month), str(s.days), f"{s.mean_min_temp:.1f}", f"{s.mean_pressure:.1f}"])
        for s in stats
    ]
    return f"<table>{''.join(rows)}</table>"


def _bars(stats: list[MonthStat], key: str, label: str, width: int = 640, height: int = 220) -> str:
    pad = 40
    vals = [getattr(s, key) for s in stats]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    slot = (width - 2 * pad) / max(1, len(stats))
    bars = []
    for i, s in enumerate(stats):
        v = getattr(s, key)
        h = (v - lo) / span * (height - 2 * pad - 10) + 10
        x = pad + slot * i + slot * 0.15
        y = height - pad - h
        bars.append(
            f'<rect class="md-bar" x="{x:.1f}" y="{y:.1f}" width="{slot * 0.7:.1f}" '
            f'height="{h:.1f}"><title>Month {s.month}: {v:.1f}</title></rect>'
            f'<text class="md-tick" x="{x + slot * 0.35:.1f}" y="{height - pad + 14}" '
            f'text-anchor="middle">{s.month}</text>'
        )
    bottom = height - pad
    axis = f'<path class="md-axis" d="M{pad},{pad} L{pad},{bottom} L{width - pad},{bottom}"/>'
    ticks = (
        f'<text class="md-tick" x="{pad - 4}" y="{pad + 4}" text-anchor="end">{hi:.0f}</text>'
        f'<text class="md-tick" x="{pad - 4}" y="{bottom + 4}" text-anchor="end">{lo:.0f}</text>'
    )
    aria = html.escape(f"{label} by Martian month")
    return (
        f'<svg class="md-chart" viewBox="0 0 {width} {height}" role="img" aria-label="{aria}">'
        f"{axis}{''.join(bars)}{ticks}</svg>"
    )


def render_html(data: dict[str, object], pages: str, provenance: str) -> str:
    articles = _articles(data)
    obs = _observations(data)
    stats = by_month(obs)
    ex = extremes(stats)
    first, last, n = date_range(obs)
    year = year_length_days(obs)
    sources = data["sources"]
    if not isinstance(sources, dict):
        msg = "snapshot sources must be an object"
        raise ValueError(msg)
    tpl = Template((TEMPLATES / "page.html").read_text(encoding="utf-8"))
    kpi = {
        "articles": len(articles),
        "observations": n,
        "first": first,
        "last": last,
        "coldest": ex["coldest"].month,
        "warmest": ex["warmest"].month,
        "lowestPressure": ex["lowest_pressure"].month,
        "highestPressure": ex["highest_pressure"].month,
        "yearDays": year,
        "fetchedAt": data["fetched_at"],
        "provenance": provenance,
    }
    return tpl.substitute(
        pages=html.escape(pages),
        provenance=html.escape(provenance),
        fetched=html.escape(str(data["fetched_at"])),
        news_url=html.escape(str(sources["news"])),
        weather_url=html.escape(str(sources["weather"])),
        n_articles=str(len(articles)),
        n_obs=f"{n:,}",
        first=first,
        last=last,
        news=_news_list(articles),
        month_table=_month_table(stats),
        temp_chart=_bars(stats, "mean_min_temp", "Mean minimum temperature (°C)"),
        pressure_chart=_bars(stats, "mean_pressure", "Mean pressure (Pa)"),
        coldest=str(ex["coldest"].month),
        coldest_t=f"{ex['coldest'].mean_min_temp:.1f}",
        warmest=str(ex["warmest"].month),
        warmest_t=f"{ex['warmest'].mean_min_temp:.1f}",
        low_p=str(ex["lowest_pressure"].month),
        low_p_v=f"{ex['lowest_pressure'].mean_pressure:.1f}",
        high_p=str(ex["highest_pressure"].month),
        high_p_v=f"{ex['highest_pressure'].mean_pressure:.1f}",
        year=f"{year:.1f}",
        report_json=json.dumps(kpi),
    )


def write_report(
    out: Path,
    snapshot: Path,
    provenance: str,
    pages: str = "https://freddricklogan.github.io/WebScraping-Mars/",
) -> Path:
    data = load_snapshot(snapshot)
    out.mkdir(parents=True, exist_ok=True)
    (out / "src").mkdir(exist_ok=True)
    shutil.copy(SHELL_DIR / "exec-shell.css", out / "src" / "exec-shell.css")
    shutil.copy(SHELL_DIR / "exec-shell.js", out / "src" / "exec-shell.js")
    shutil.copy(PKG / "report.js", out / "src" / "report.js")
    shutil.copy(TEMPLATES / "report.css", out / "src" / "report.css")
    (out / "index.html").write_text(render_html(data, pages, provenance), encoding="utf-8")
    shutil.copy(snapshot, out / "snapshot.json")
    return out / "index.html"

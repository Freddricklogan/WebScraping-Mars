"""Command-line entry point: `marsdash scrape --out data/snapshot.json` and `marsdash report`."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from .report import write_report
from .scrape import NEWS_URL, WEATHER_URL, fetch, snapshot

app = typer.Typer(add_completion=False, help="Mars news and weather dashboard.")


@app.callback()
def main() -> None:
    """Mars news and weather dashboard."""


@app.command()
def scrape(
    out: Path = typer.Option(Path("data") / "snapshot.json", help="Where to write the snapshot."),
) -> None:
    """Fetch both sources, parse them, and write the snapshot JSON; exits non-zero on failure."""
    data = snapshot(fetch(NEWS_URL), fetch(WEATHER_URL))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    articles, obs = data["articles"], data["observations"]
    if isinstance(articles, list) and isinstance(obs, list):
        print(f"wrote {out}: {len(articles)} articles, {len(obs)} observations")


@app.command()
def report(
    out: Path = typer.Option(Path("dist"), help="Output directory for the static dashboard."),
    snapshot_path: Path = typer.Option(
        Path("data") / "snapshot.json", "--snapshot", help="Snapshot JSON to render."
    ),
    live: bool = typer.Option(False, help="Try a live scrape first and fall back to the snapshot."),
) -> None:
    """Render the dashboard from a snapshot, optionally refreshing it live first."""
    provenance = f"committed snapshot {snapshot_path}"
    source = snapshot_path
    if live:
        try:
            data = snapshot(fetch(NEWS_URL), fetch(WEATHER_URL))
            source = out / "live-snapshot.json"
            out.mkdir(parents=True, exist_ok=True)
            source.write_text(json.dumps(data, indent=1), encoding="utf-8")
            provenance = "live scrape in this build"
        except Exception as err:  # any network or parse failure falls back, and the page says so
            provenance = f"committed snapshot (live scrape failed: {type(err).__name__})"
    path = write_report(out, source, provenance)
    print(f"wrote {path} from {provenance}")


if __name__ == "__main__":
    app()

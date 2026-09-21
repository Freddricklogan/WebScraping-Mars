import json
from pathlib import Path

import pytest

from marsdash.report import load_snapshot, write_report
from marsdash.scrape import parse_news, parse_weather, snapshot
from marsdash.weather import by_month, date_range, extremes, year_length_days

FIX = Path(__file__).resolve().parent / "fixtures"
NEWS = (FIX / "news.html").read_text(encoding="utf-8")
WEATHER = (FIX / "temperature.html").read_text(encoding="utf-8")


def test_parse_news_fixture() -> None:
    a = parse_news(NEWS)
    assert len(a) == 15
    assert a[0].date == "November 9, 2022"
    assert a[0].title.startswith("NASA's MAVEN Observes")
    assert a[0].teaser.startswith("For the first time")
    with pytest.raises(ValueError, match="no articles"):
        parse_news("<html><body><p>nothing</p></body></html>")


def test_parse_weather_fixture_and_rejections() -> None:
    o = parse_weather(WEATHER)
    assert len(o) == 1867
    assert o[0].__dict__ == {
        "id": 2,
        "terrestrial_date": "2012-08-16",
        "sol": 10,
        "ls": 155,
        "month": 6,
        "min_temp": -75.0,
        "pressure": 739.0,
    }
    assert date_range(o) == ("2012-08-16", "2018-02-27", 1867)
    with pytest.raises(ValueError, match="unexpected weather table header"):
        parse_weather("<table><tr><th>a</th></tr></table>")
    good_head = (
        "<table><tr>"
        + "".join(
            f"<th>{h}</th>"
            for h in ["id", "terrestrial_date", "sol", "ls", "month", "min_temp", "pressure"]
        )
        + "</tr>"
    )
    with pytest.raises(ValueError, match="no weather rows"):
        parse_weather(good_head + "</table>")
    with pytest.raises(ValueError, match="cells"):
        parse_weather(good_head + '<tr class="data-row"><td>1</td></tr></table>')

    def row(*cells: str) -> str:
        return '<tr class="data-row">' + "".join(f"<td>{c}</td>" for c in cells) + "</tr></table>"

    with pytest.raises(ValueError, match="month 13"):
        parse_weather(good_head + row("1", "2012-08-16", "1", "0", "13", "-70", "700"))
    with pytest.raises(ValueError):
        parse_weather(good_head + row("1", "16/08/2012", "1", "0", "1", "-70", "700"))


def test_weather_statistics_reproduce_the_classic_answers() -> None:
    o = parse_weather(WEATHER)
    stats = by_month(o)
    assert [s.month for s in stats] == list(range(1, 13))
    assert sum(s.days for s in stats) == 1867
    ex = extremes(stats)
    assert (ex["coldest"].month, ex["warmest"].month) == (3, 8)
    assert (ex["lowest_pressure"].month, ex["highest_pressure"].month) == (6, 9)
    assert ex["coldest"].mean_min_temp == pytest.approx(-83.3, abs=0.05)
    assert year_length_days(o) == pytest.approx(687.0, abs=1.0)  # Mars: 686.98 Earth days
    with pytest.raises(ValueError, match="no monthly"):
        extremes([])
    with pytest.raises(ValueError, match="at least two"):
        year_length_days(o[:1])


def test_year_length_fallback_with_fewer_than_two_wraps() -> None:
    o = parse_weather(WEATHER)
    first_year = [x for x in o if x.terrestrial_date < "2014-01-01"]
    est = year_length_days(first_year)
    assert 600 < est < 780  # the days-per-degree fallback is rough but in range


def test_snapshot_and_report(tmp_path: Path) -> None:
    data = snapshot(NEWS, WEATHER, fetched_at="2026-09-21T00:00:00+00:00")
    assert data["fetched_at"] == "2026-09-21T00:00:00+00:00"
    snap = tmp_path / "snapshot.json"
    snap.write_text(json.dumps(data))
    assert load_snapshot(snap)["fetched_at"] == data["fetched_at"]
    out = write_report(tmp_path / "dist", snap, provenance="test snapshot")
    page = out.read_text(encoding="utf-8")
    assert "Content-Security-Policy" in page and "test snapshot" in page and "onclick" not in page
    assert "$" not in page.replace("$pages", "")
    assert (tmp_path / "dist" / "snapshot.json").exists()
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"fetched_at": "x"}))
    with pytest.raises(ValueError, match="missing"):
        load_snapshot(bad)
    bad.write_text(
        json.dumps({"fetched_at": "x", "sources": {}, "articles": "no", "observations": []})
    )
    with pytest.raises(ValueError, match="must be a list"):
        write_report(tmp_path / "d2", bad, provenance="x")


def test_fetch_uses_requests_and_raises_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    import requests

    from marsdash import scrape

    class Resp:
        text = "<html></html>"
        status_code = 500

        def raise_for_status(self) -> None:
            msg = "500"
            raise RuntimeError(msg)

    monkeypatch.setattr(requests, "get", lambda *_a, **_k: Resp())
    with pytest.raises(RuntimeError):
        scrape.fetch("https://example.org")

    class Ok(Resp):
        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(requests, "get", lambda *_a, **_k: Ok())
    assert scrape.fetch("https://example.org") == "<html></html>"


def test_report_rejects_bad_sources(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        json.dumps(
            {
                "fetched_at": "x",
                "sources": [],
                "articles": [],
                "observations": [
                    {
                        "id": 1,
                        "terrestrial_date": "2012-08-16",
                        "sol": 1,
                        "ls": 0,
                        "month": 1,
                        "min_temp": -70.0,
                        "pressure": 700.0,
                    },
                    {
                        "id": 2,
                        "terrestrial_date": "2012-08-17",
                        "sol": 2,
                        "ls": 1,
                        "month": 1,
                        "min_temp": -70.0,
                        "pressure": 700.0,
                    },
                ],
            }
        )
    )
    with pytest.raises(ValueError, match="sources"):
        write_report(tmp_path / "d3", bad, provenance="x")

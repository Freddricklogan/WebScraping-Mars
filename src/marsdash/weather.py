"""Statistics over the Curiosity REMS observations (the exercise's classic questions, computed)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .scrape import Observation


@dataclass(frozen=True)
class MonthStat:
    month: int
    days: int
    mean_min_temp: float
    mean_pressure: float


def by_month(obs: list[Observation]) -> list[MonthStat]:
    out: list[MonthStat] = []
    for m in range(1, 13):
        rows = [o for o in obs if o.month == m]
        if rows:
            out.append(
                MonthStat(
                    m,
                    len(rows),
                    float(np.mean([o.min_temp for o in rows])),
                    float(np.mean([o.pressure for o in rows])),
                )
            )
    return out


def extremes(stats: list[MonthStat]) -> dict[str, MonthStat]:
    if not stats:
        msg = "no monthly statistics"
        raise ValueError(msg)
    return {
        "coldest": min(stats, key=lambda s: s.mean_min_temp),
        "warmest": max(stats, key=lambda s: s.mean_min_temp),
        "lowest_pressure": min(stats, key=lambda s: s.mean_pressure),
        "highest_pressure": max(stats, key=lambda s: s.mean_pressure),
    }


def year_length_days(obs: list[Observation]) -> float:
    """Estimate the Martian year in Earth days from the solar-longitude cycle: the mean span of
    terrestrial days between successive passages through Ls = 0 (northern spring equinox)."""
    rows = sorted(obs, key=lambda o: o.sol)
    if len(rows) < 2:
        msg = "need at least two observations"
        raise ValueError(msg)
    dates = np.array([np.datetime64(o.terrestrial_date) for o in rows])
    ls = np.array([o.ls for o in rows])
    # A wrap from high Ls (near 360) to low Ls marks a new Martian year.
    wraps = np.where(np.diff(ls) < -180)[0] + 1
    if len(wraps) < 2:
        # Fall back to the total Ls travelled: days per degree times 360.
        total_deg = float(ls[-1] - ls[0] + 360 * len(wraps))
        span = float((dates[-1] - dates[0]) / np.timedelta64(1, "D"))
        return span / total_deg * 360.0
    spans = np.diff(dates[wraps]) / np.timedelta64(1, "D")
    return float(np.mean(spans))


def date_range(obs: list[Observation]) -> tuple[str, str, int]:
    rows = sorted(obs, key=lambda o: o.terrestrial_date)
    return rows[0].terrestrial_date, rows[-1].terrestrial_date, len(rows)

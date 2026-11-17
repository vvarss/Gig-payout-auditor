"""
checks.py  --  Step 2 of the pipeline: numbers -> flags (plain Python, NO AI).

Three checks:
  1. SUM CHECK        trip_pay + return_pay should equal the total shown.
  2. RATE CHECK       trip pay per km far BELOW the typical (median) rate.
  3. RETURN-PAY CHECK a long trip got no return pay, though similar long trips did.

Run:
  python checks.py             -> uses data/synthetic/answers.json (no API needed)
  python checks.py extracted   -> uses data/extracted.json (real Claude extraction)
"""
import json
import os
import sys

import pandas as pd

ANSWERS_FILE = os.path.join("data", "synthetic", "answers.json")
EXTRACTED_FILE = os.path.join("data", "extracted.json")

SUM_TOLERANCE = 0.05        # rupees; allows 1-paisa rounding differences
RATE_DROP = 0.25            # flag if pay per km is 25% below the median
# ---------------------------------------------------------------------


def load_trips(source="answers"):
    """Return a table with ONE ROW PER TRIP and the same column names either way."""
    if source == "extracted":
        with open(EXTRACTED_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        rows = [{
            "file": name,
            "km": r.get("distance_km"),
            "mins": r.get("trip_time_mins"),
            "trip_pay": r.get("trip_pay"),
            "return_pay": r.get("long_distance_return_pay"),
            "total": r.get("total_earnings"),
        } for name, r in raw.items()]
    else:
        with open(ANSWERS_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        rows = [{
            "file": r["file"],
            "km": r["km"],
            "mins": r["mins"],
            "trip_pay": r["shown_trip_pay"],
            "return_pay": r["shown_return_pay"],
            "total": r["shown_total"],
        } for r in raw]
    df = pd.DataFrame(rows)
    df["return_pay"] = df["return_pay"].fillna(0.0)     # no line on screen = 0
    return df


def check_sum(df):
    flags = []
    for _, t in df.iterrows():
        parts = round(t.trip_pay + t.return_pay, 2)
        diff = round(t.total - parts, 2)
        if abs(diff) > SUM_TOLERANCE:
            flags.append({
                "file": t.file, "check": "sum",
                "rupees": abs(diff),
                "detail": f"Parts add up to {parts:.2f} but the screen shows {t.total:.2f} "
                          f"(difference {diff:+.2f}).",
            })
    return flags


def check_rate(df):
    """Flag trips paid well BELOW the typical rate. (Short trips naturally earn more
    per km because of the base fare, so we only look at the low side.)"""
    flags = []
    per_km = df["trip_pay"] / df["km"]
    median = per_km.median()
    for i, t in df.iterrows():
        if per_km[i] < median * (1 - RATE_DROP):
            expected = median * t.km
            flags.append({
                "file": t.file, "check": "rate",
                "rupees": round(expected - t.trip_pay, 2),
                "detail": f"Trip pay is {per_km[i]:.2f}/km for {t.km} km, while the "
                          f"typical rate is {median:.2f}/km (about {expected - t.trip_pay:.0f} "
                          f"rupees less than usual).",
            })
    return flags


def check_return_pay(df):
    """Learn from the data: what is the shortest trip that DID get return pay and at
    what rate? Then flag longer trips that got none."""
    got = df[df["return_pay"] > 0]
    if got.empty:
        return []
    min_km = got["km"].min()
    rate = (got["return_pay"] / got["km"]).median()
    flags = []
    for _, t in df.iterrows():
        if t.km >= min_km and t.return_pay == 0:
            flags.append({
                "file": t.file, "check": "return_pay",
                "rupees": round(rate * t.km, 2),
                "detail": f"{t.km} km trip has no long-distance return pay, but trips of "
                          f"{min_km} km or more usually get about {rate:.2f}/km "
                          f"(around {rate * t.km:.0f} rupees).",
            })
    return flags


def run_all_checks(df):
    flags = check_sum(df) + check_rate(df) + check_return_pay(df)
    return sorted(flags, key=lambda f: f["rupees"], reverse=True)


# ---------------------------------------------------------------------
# Scoring against the answer key (only for the synthetic test set)
# ---------------------------------------------------------------------
def evaluate(flags, df):
    with open(ANSWERS_FILE, encoding="utf-8") as f:
        key = {r["file"]: r["error"] for r in json.load(f)}
    flagged = {f["file"] for f in flags}
    in_scope = [name for name in df["file"] if name in key]

    planted = [n for n in in_scope if key[n] != "none"]
    normal = [n for n in in_scope if key[n] == "none"]
    caught = [n for n in planted if n in flagged]
    missed = [n for n in planted if n not in flagged]
    false_alarms = [n for n in normal if n in flagged]

    print("\n=== EVALUATION ===")
    print(f"Planted errors caught : {len(caught)} of {len(planted)}")
    for n in missed:
        print(f"  MISSED      {n}  ({key[n]})")
    print(f"False alarms          : {len(false_alarms)} of {len(normal)} normal trips")
    for n in false_alarms:
        print(f"  FALSE ALARM {n}")


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "answers"
    trips = load_trips(source)
    results = run_all_checks(trips)

    print(f"Checked {len(trips)} trips, found {len(results)} flag(s):\n")
    for f in results:
        print(f"[{f['check']:<10}] {f['file']}: {f['detail']}")
    evaluate(results, trips)

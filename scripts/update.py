#!/usr/bin/env python3
"""Folds TfL's live Santander Cycles counts into typical availability per 15-minute slot.

Reads the current profiles.json, adds one sample from the TfL BikePoint feed, and writes it back.
Rows are [dow, slot, samples, bikes x10, ebikes x10, docks x10, empty %, full %], London time,
dow 0 = Sunday, slot 0-95.
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TFL_URL = "https://api.tfl.gov.uk/BikePoint"
MIN_WEIGHT = 0.08  # after ~12 samples, newer days count more so profiles follow the seasons


def fetch_tfl():
    request = urllib.request.Request(TFL_URL, headers={
        "User-Agent": "tfl-bike-availability/1.0 (github.com/GeorgeCC-hardware/tfl-bike-availability)",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def main(path):
    try:
        with open(path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    stations = data.get("stations") or {}

    now = datetime.now(ZoneInfo("Europe/London"))
    dow = (now.weekday() + 1) % 7
    slot = now.hour * 4 + now.minute // 15

    updated = 0
    for point in fetch_tfl():
        props = {p["key"]: p["value"] for p in point.get("additionalProperties", [])}
        if props.get("Installed") == "false" or props.get("Locked") == "true":
            continue
        bikes = int(props.get("NbBikes") or 0)
        ebikes = int(props.get("NbEBikes") or 0)
        docks = int(props.get("NbEmptyDocks") or 0)
        sample = [bikes, ebikes, docks, 1.0 if bikes == 0 else 0.0, 1.0 if docks == 0 else 0.0]

        rows = stations.setdefault(point["id"], [])
        row = next((r for r in rows if r[0] == dow and r[1] == slot), None)
        if row is None:
            rows.append([dow, slot, 1, bikes * 10, ebikes * 10, docks * 10,
                         round(sample[3] * 100), round(sample[4] * 100)])
        else:
            weight = max(1 / (row[2] + 1), MIN_WEIGHT)
            current = [row[3] / 10, row[4] / 10, row[5] / 10, row[6] / 100, row[7] / 100]
            blended = [c + (s - c) * weight for c, s in zip(current, sample)]
            row[2] += 1
            row[3:8] = [round(blended[0] * 10), round(blended[1] * 10), round(blended[2] * 10),
                        round(blended[3] * 100), round(blended[4] * 100)]
        updated += 1

    for rows in stations.values():
        rows.sort(key=lambda r: (r[0], r[1]))
    out = {
        "version": 1,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "stations": dict(sorted(stations.items())),
    }
    with open(path, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Updated {updated} stations for dow={dow} slot={slot}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "profiles.json")

#!/usr/bin/env python3
"""
Fetch the latest Gaza casualty statistics from the Tech for Palestine
"Palestine Datasets" API (https://data.techforpalestine.org).

The API aggregates the daily casualty reports published by the Gaza
Ministry of Health (via Telegram) and cross-references them with UN OCHA
figures. It is updated daily and is the most reliable machine-readable
source available for these numbers.

Endpoints used:
  - https://data.techforpalestine.org/api/v3/summary.json
      Latest cumulative values (killed, injured, children, women, press,
      medical staff, civil defence, massacres) for Gaza, the West Bank
      and Lebanon, plus the known-by-name victim list summary.

Figures that are NOT available from this API (displacement, hospital
functionality, food insecurity) are kept as manually-maintained values in
MANUAL_FIGURES below, sourced from UN OCHA flash updates. Update them
from https://www.ochaopt.org/ when newer figures are published.

If the API is unreachable, the previously saved data/latest_stats.json is
kept untouched so the repository never regresses to fabricated numbers.
"""

import json
import os
import sys
from datetime import datetime

import requests

SUMMARY_URL = "https://data.techforpalestine.org/api/v3/summary.json"
DATA_FILE = "data/latest_stats.json"
REQUEST_TIMEOUT = 30

# Figures NOT exposed by the API. Sourced from UN OCHA Gaza flash updates
# (https://www.ochaopt.org/). Update manually when OCHA publishes new ones.
MANUAL_FIGURES = {
    "displaced_people": "1.9M+",          # ~90% of population, per UN OCHA
    "operational_hospitals": "15/36",     # partially functional, per WHO
    "food_insecurity": "93%",             # acute food insecurity, per IPC
    "water_access": "15%",                # population with safe water access
}

CONFLICT_START = datetime(2023, 10, 7)


def fmt(number):
    """Format a count for display, e.g. 74016 -> '74,016+'."""
    return f"{int(number):,}+"


def fetch_summary():
    """Fetch the summary dataset, returning the parsed JSON or None."""
    try:
        response = requests.get(SUMMARY_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"ERROR: could not fetch {SUMMARY_URL}: {e}")
        return None


def build_stats(summary):
    """Build the statistics dict from the API summary payload."""
    gaza = summary["gaza"]
    killed = gaza["killed"]
    west_bank = summary.get("west_bank", {})
    known = summary.get("known_killed_in_gaza", {})

    # Sanity check: refuse implausible payloads instead of publishing them.
    if killed["total"] < 30000:
        raise ValueError(f"implausible total killed: {killed['total']}")

    stats = {
        # Core Gaza figures (Gaza Ministry of Health daily reports)
        "total_deaths": fmt(killed["total"]),
        "children_deaths": fmt(killed["children"]),
        "women_deaths": fmt(killed["women"]),
        "total_injured": fmt(gaza["injured"]["total"]),
        "press_killed": fmt(killed["press"]),
        "medical_staff_killed": fmt(killed["medical"]),
        "civil_defence_killed": fmt(killed["civil_defence"]),
        "massacres": fmt(gaza["massacres"]),
        # Manually maintained OCHA figures (see MANUAL_FIGURES above)
        **MANUAL_FIGURES,
        # West Bank context (same source, different dataset)
        "west_bank_killed": fmt(west_bank.get("killed", {}).get("total", 0)),
        "west_bank_children_killed": fmt(west_bank.get("killed", {}).get("children", 0)),
        # Known-by-name victims list (always lower than the headcount above)
        "known_named_victims": fmt(known.get("records", 0)),
        # Metadata
        "last_data_update": gaza["last_update"],
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M UTC"),
        "days_of_conflict": (datetime.now() - CONFLICT_START).days,
        "fetch_timestamp": datetime.now().isoformat(),
        "source": "Tech for Palestine - Palestine Datasets (Gaza MoH / UN OCHA)",
        "source_url": SUMMARY_URL,
        "sources": [
            "Gaza Ministry of Health",
            "Tech for Palestine Datasets",
            "UN OCHA",
            "WHO",
        ],
        "update_frequency": "hourly",
        "data_verification": "cross-referenced by Tech for Palestine",
    }

    # Famine / aid-seeker figures are present in the API only when reported.
    famine = gaza.get("famine", {})
    if famine.get("total") is not None:
        stats["starvation_deaths"] = fmt(famine["total"])
    aid_seeker = gaza.get("aid_seeker", {})
    if aid_seeker.get("killed") is not None:
        stats["aid_seekers_killed"] = fmt(aid_seeker["killed"])

    return stats


def save_statistics():
    """Fetch statistics and save them to data/latest_stats.json."""
    summary = fetch_summary()
    if summary is None:
        if os.path.exists(DATA_FILE):
            print(f"Keeping existing {DATA_FILE} (API unreachable).")
            return None
        print("ERROR: no API data and no existing statistics file.")
        sys.exit(1)

    try:
        stats = build_stats(summary)
    except (KeyError, ValueError) as e:
        print(f"ERROR: unexpected API payload: {e}")
        if os.path.exists(DATA_FILE):
            print(f"Keeping existing {DATA_FILE}.")
            return None
        sys.exit(1)

    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"Statistics updated at {stats['fetch_timestamp']}")
    print(f"Data through {stats['last_data_update']} | "
          f"killed: {stats['total_deaths']}, injured: {stats['total_injured']}")
    print(f"Data saved to {DATA_FILE}")
    return stats


if __name__ == "__main__":
    save_statistics()

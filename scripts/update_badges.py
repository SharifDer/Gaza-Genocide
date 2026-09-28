#!/usr/bin/env python3
"""
Update README badges and the live statistics table with the latest
statistics from data/latest_stats.json (produced by fetch_statistics.py).
"""

import json
import re
from datetime import datetime

STATS_FILE = "data/latest_stats.json"
README_FILE = "README.md"

BADGES = [
    # (key in stats JSON, badge label, color)
    ("total_deaths", "Death%20Toll", "red"),
    ("children_deaths", "Children%20Killed", "orange"),
    ("women_deaths", "Women%20Killed", "purple"),
    ("total_injured", "Injured", "yellow"),
    ("press_killed", "Journalists%20Killed", "critical"),
    ("medical_staff_killed", "Medical%20Staff%20Killed", "lightgrey"),
    ("displaced_people", "Displaced", "blue"),
    ("operational_hospitals", "Hospitals%20Operational", "green"),
]

# Rows of the "LIVE STATISTICS TABLE" in README.md:
# (row label, key in stats JSON)
TABLE_ROWS = [
    ("Total Deaths", "total_deaths"),
    ("Children Killed", "children_deaths"),
    ("Women Killed", "women_deaths"),
    ("Injured", "total_injured"),
    ("Journalists Killed", "press_killed"),
    ("Medical Staff Killed", "medical_staff_killed"),
    ("Displaced", "displaced_people"),
    ("Hospitals", "operational_hospitals"),
]

# Placeholders in the dashboard HTML templates -> key in stats JSON.
# Values are injected at update time so the numbers are visible to
# search engines and AI crawlers as plain static text (no JS needed).
# The generated pages (index.html, ar.html) are what GitHub Pages serves;
# templates/ holds the source with {{PLACEHOLDER}} tokens.
HTML_TEMPLATES = {
    "templates/index.html": "index.html",
    "templates/ar.html": "ar.html",
}
HTML_PLACEHOLDERS = {
    "TOTAL_DEATHS": "total_deaths",
    "CHILDREN_DEATHS": "children_deaths",
    "WOMEN_DEATHS": "women_deaths",
    "TOTAL_INJURED": "total_injured",
    "PRESS_KILLED": "press_killed",
    "MEDICAL_KILLED": "medical_staff_killed",
    "MASSACRES": "massacres",
    "DISPLACED": "displaced_people",
    "HOSPITALS": "operational_hospitals",
    "KNOWN_NAMED": "known_named_victims",
    "LAST_DATA_UPDATE": "last_data_update",
    "LAST_UPDATED": "last_updated",
    "DAYS_OF_CONFLICT": "days_of_conflict",
}

# Raw numeric placeholders used by the dashboard charts.
HTML_NUMERIC = {
    "N_KILLED": "total_deaths",
    "N_CHILDREN": "children_deaths",
    "N_WOMEN": "women_deaths",
}


def to_int(value):
    """'74,018+' -> 74018"""
    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else 0


def load_latest_stats():
    """Load the latest statistics from JSON file"""
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No statistics file found at {STATS_FILE}. Run fetch_statistics.py first.")
        return None
    except Exception as e:
        print(f"Error loading statistics: {e}")
        return None


def create_badge_url(label, value, color):
    """Create a shields.io badge URL"""
    clean_value = str(value).replace("+", "%2B").replace(" ", "%20")
    return f"https://img.shields.io/badge/{label}-{clean_value}-{color}?style=for-the-badge"


def update_badges(content, stats):
    """Replace shields.io badge URLs for each configured label."""
    for key, label, color in BADGES:
        value = stats.get(key, "Loading...")
        new_url = create_badge_url(label, value, color)
        # Match the existing badge URL for this label, up to the closing ')'.
        pattern = rf"https://img\.shields\.io/badge/{re.escape(label)}-[^)]*"
        content, n = re.subn(pattern, new_url, content)
        if n == 0:
            print(f"WARNING: badge '{label}' not found in README")

    # The "Last Updated" badge carries a timestamp, not a stat.
    timestamp = stats.get("last_updated", "")
    new_url = create_badge_url("Last%20Updated", timestamp, "blue")
    content, n = re.subn(
        r"https://img\.shields\.io/badge/Last%20Updated-[^)]*", new_url, content
    )
    if n == 0:
        print("WARNING: 'Last Updated' badge not found in README")
    return content


def update_table(content, stats):
    """Update the LIVE STATISTICS TABLE rows with current values."""
    last_updated = stats.get("last_updated", "")
    for label, key in TABLE_ROWS:
        value = stats.get(key)
        if value is None:
            continue
        pattern = rf"\| {re.escape(label)} \| [^|]+ \| [^|]+ \|"
        replacement = f"| {label} | {value} | {last_updated} |"
        content, n = re.subn(pattern, replacement, content)
        if n == 0:
            print(f"WARNING: table row '{label}' not found in README")
    return content


def update_readme_badges():
    """Update the README.md file with new badge URLs and table values"""
    stats = load_latest_stats()
    if not stats:
        return False

    try:
        with open(README_FILE, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {README_FILE}: {e}")
        return False

    content = update_badges(content, stats)
    content = update_table(content, stats)

    # Update the last updated timestamp at the bottom of the README
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    content = re.sub(
        r"\*\*Last Updated\*\*: .*",
        f"**Last Updated**: {timestamp}",
        content,
    )

    try:
        with open(README_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"README badges and table updated successfully at {timestamp}")
        return True
    except Exception as e:
        print(f"Error writing {README_FILE}: {e}")
        return False


def update_html_pages(stats):
    """Generate the dashboard HTML pages from templates/ with the
    current statistics injected as static text (visible to search
    engines and AI crawlers), while the charts stay interactive via
    JavaScript. Returns True if every page was generated cleanly.
    """
    ok = True
    for template_path, out_path in HTML_TEMPLATES.items():
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"WARNING: {template_path} not found, skipping")
            ok = False
            continue

        for placeholder, key in HTML_PLACEHOLDERS.items():
            value = stats.get(key)
            if value is None:
                continue
            content = content.replace("{{" + placeholder + "}}", str(value))

        for placeholder, key in HTML_NUMERIC.items():
            token = "{{" + placeholder + "}}"
            if token in content:
                content = content.replace(token, str(to_int(stats.get(key, 0))))

        remaining = re.findall(r"\{\{[A-Z_]+\}\}", content)
        if remaining:
            print(f"WARNING: {out_path} has unfilled placeholders: {sorted(set(remaining))}")
            ok = False

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{out_path} generated from {template_path}")
    return ok


if __name__ == "__main__":
    print("Updating README badges...")
    stats = load_latest_stats()
    success = update_readme_badges()
    if stats:
        update_html_pages(stats)

    if success:
        print("Badge update completed successfully!")
    else:
        print("Badge update failed!")

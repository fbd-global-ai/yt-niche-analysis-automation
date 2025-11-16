"""
Niche Analysis Automation for YouTube

Steps:
1. Put your niches (one per line) into a file named 'niches.txt'
2. Get a YouTube Data API v3 key from Google Cloud
3. Replace YOUTUBE_API_KEY with your own key
4. Run: python niche_analysis_automation.py
"""

import json
import csv
import time
from pathlib import Path
from urllib import parse, request


# ================== CONFIG ==================

YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # <-- PUT YOUR API KEY HERE
MAX_RESULTS_PER_QUERY = 25             # how many videos to fetch per niche
INPUT_FILE = "niches.txt"
OUTPUT_FILE = "niche_report.csv"
REQUEST_SLEEP_SECONDS = 1              # small delay to avoid quota issues


# ================== YOUTUBE HELPERS ==================

def build_search_url(query: str, max_results: int = 25) -> str:
    """Build YouTube Data API search URL for a given query."""
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }
    return f"{base_url}?{parse.urlencode(params)}"


def fetch_json(url: str) -> dict:
    """Send GET request and parse JSON response."""
    with request.urlopen(url) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def analyze_niche(query: str) -> dict:
    """
    Analyze a single niche using YouTube search results.

    Returns a dict with:
    - niche
    - video_count
    - unique_channel_count
    - opportunity_score (simple heuristic)
    """
    url = build_search_url(query, MAX_RESULTS_PER_QUERY)
    data = fetch_json(url)

    items = data.get("items", [])
    video_count = len(items)

    channel_ids = {item["snippet"]["channelId"] for item in items if "snippet" in item}
    unique_channel_count = len(channel_ids)

    # Simple opportunity score:
    # fewer channels + more videos => potentially interesting + competitive
    # We invert channel count to reward niches with fewer active creators
    if unique_channel_count == 0:
        opportunity_score = 0
    else:
        opportunity_score = round((video_count / unique_channel_count), 2)

    return {
        "niche": query,
        "video_count": video_count,
        "unique_channel_count": unique_channel_count,
        "opportunity_score": opportunity_score,
    }


# ================== FILE HELPERS ==================

def read_niches_from_file(file_path: str) -> list:
    """Read niches from a text file (one niche per line)."""
    path = Path(file_path)
    if not path.exists():
        print(f"[ERROR] Input file '{file_path}' not found.")
        print("Create a file named 'niches.txt' with one niche per line.")
        return []

    with path.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines


def save_results_to_csv(results: list, file_path: str) -> None:
    """Save analysis results to a CSV file."""
    fieldnames = ["niche", "video_count", "unique_channel_count", "opportunity_score"]
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)


# ================== MAIN WORKFLOW ==================

def main():
    print("=== YouTube Niche Analysis Automation ===")

    if YOUTUBE_API_KEY == "AIzaSyCoqz_WZaGbxhXkMpHo2s-T46qygmrmrHo":
        print("[ERROR] Please set your YOUTUBE_API_KEY in the script.")
        return

    niches = read_niches_from_file(INPUT_FILE)
    if not niches:
        return

    all_results = []

    for index, niche in enumerate(niches, start=1):
        print(f"\n[{index}/{len(niches)}] Analyzing niche: {niche}")
        try:
            result = analyze_niche(niche)
            all_results.append(result)

            print(f"  Video count          : {result['video_count']}")
            print(f"  Unique channel count : {result['unique_channel_count']}")
            print(f"  Opportunity score    : {result['opportunity_score']}")
        except Exception as e:
            print(f"  [ERROR] Failed to analyze niche '{niche}': {e}")

        # Small delay between requests
        time.sleep(REQUEST_SLEEP_SECONDS)

    # Sort by opportunity_score (descending)
    all_results.sort(key=lambda x: x["opportunity_score"], reverse=True)

    save_results_to_csv(all_results, OUTPUT_FILE)
    print(f"\n=== Done! Results saved to '{OUTPUT_FILE}' ===")
    print("Tip: Open this CSV file in Excel / Google Sheets to compare niches easily.")


if __name__ == "__main__":
    main()

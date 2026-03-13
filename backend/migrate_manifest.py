"""
migrate_manifest.py
One-off migration: converts existing games.json + per-game FTR files
into per-day summary FTRs, per-day JSON files, and index.json.

Run from the project root:
    python3 backend/migrate_manifest.py
"""

import glob
import json
import os
import sys

import pandas as pd
import pyarrow.feather as feather

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
GAMES_JSON = os.path.join(DATA_DIR, 'games.json')

SUMMARY_COLUMNS = [
    'gamePk', 'officialDate', 'season', 'seriesDescription', 'gameDescription',
    'venue', 'homeTeam', 'awayTeam', 'homeFinalScore', 'awayFinalScore',
    'defenseScore', 'offenseScore', 'thrillScore', 'superlatives', 'filePath',
]


def build_summary_from_game_ftr(ftr_path: str, gamepk: str, date_str: str) -> dict | None:
    """Read a full play-by-play FTR and return a single summary dict."""
    try:
        df = feather.read_table(ftr_path).to_pandas()
        if df.empty:
            return None
        last = df.iloc[-1]
        first = df.iloc[0]
        web_path = ftr_path.replace(os.path.normpath(os.path.join(DATA_DIR, '..')) + os.sep, '')
        web_path = web_path.replace('\\', '/')  # normalise on Windows

        return {
            'gamePk': str(gamepk),
            'officialDate': str(last.get('officialDate', date_str)),
            'season': str(last.get('season', '')),
            'seriesDescription': str(last.get('seriesDescription', '')),
            'gameDescription': str(last.get('gameDescription', '')),
            'venue': str(last.get('venue', '')),
            'homeTeam': str(last.get('homeTeam', '')),
            'awayTeam': str(last.get('awayTeam', '')),
            'homeFinalScore': last.get('homeScore', last.get('homeFinalScore', 0)),
            'awayFinalScore': last.get('awayScore', last.get('awayFinalScore', 0)),
            'defenseScore': float(last.get('defenseScore', 0)),
            'offenseScore': float(last.get('offenseScore', 0)),
            'thrillScore': float(last.get('thrillScore', 0)),
            'superlatives': str(last.get('superlatives', '')),
            'filePath': web_path,
        }
    except Exception as e:
        print(f"  [WARN] Could not read {ftr_path}: {e}", file=sys.stderr)
        return None


def migrate():
    if not os.path.isfile(GAMES_JSON):
        print(f"[ERROR] {GAMES_JSON} not found – nothing to migrate.", file=sys.stderr)
        sys.exit(1)

    with open(GAMES_JSON) as f:
        manifest = json.load(f)

    dates_found = []

    for date_str, ftr_paths in manifest.items():
        print(f"Processing {date_str} ({len(ftr_paths)} games)…")
        # Derive year folder
        year = date_str.split('-')[0]
        year_dir = os.path.join(DATA_DIR, year)
        os.makedirs(year_dir, exist_ok=True)

        summary_rows = []
        gamepks = []

        for web_path in ftr_paths:
            # web_path is like "data/2026/2026-03-12-831894.ftr"
            abs_ftr = os.path.normpath(os.path.join(DATA_DIR, '..', web_path))
            if not os.path.isfile(abs_ftr):
                print(f"  [WARN] Missing FTR: {abs_ftr}")
                continue

            # Extract gamePk from filename
            basename = os.path.basename(abs_ftr)  # 2026-03-12-831894.ftr
            gamepk = basename.replace('.ftr', '').split('-')[-1]

            row = build_summary_from_game_ftr(abs_ftr, gamepk, date_str)
            if row:
                summary_rows.append(row)
                gamepks.append(gamepk)

        if not summary_rows:
            print(f"  [WARN] No valid games for {date_str}, skipping.")
            continue

        # Write daily summary FTR
        summary_path = os.path.join(year_dir, f'{date_str}-summary.ftr')
        summaryDF = pd.DataFrame(summary_rows, columns=SUMMARY_COLUMNS)
        feather.write_feather(summaryDF, summary_path, compression='uncompressed')
        print(f"  → Wrote {summary_path} ({len(summary_rows)} rows)")

        # Write per-day JSON
        day_json_path = os.path.join(year_dir, f'{date_str}.json')
        with open(day_json_path, 'w') as jf:
            json.dump(gamepks, jf)
        print(f"  → Wrote {day_json_path}")

        dates_found.append(date_str)

    # Write top-level index.json
    dates_found = sorted(set(dates_found))
    index_path = os.path.join(DATA_DIR, 'index.json')
    with open(index_path, 'w') as f:
        json.dump(dates_found, f, indent=2)
    print(f"\n✓ Wrote {index_path} with {len(dates_found)} dates.")


if __name__ == '__main__':
    migrate()

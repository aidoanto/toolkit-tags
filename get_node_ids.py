#!/usr/bin/env python3
"""
get_node_ids.py

Read paths.csv, fetch each Drupal page on lifeline.org.au, extract the
data-history-node-id from the <article> tag, and write it to a third column.

Usage:
  python get_node_ids.py
  python get_node_ids.py --csv paths.csv --base-url https://www.lifeline.org.au --delay 0.2
  python get_node_ids.py --skip-existing
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://www.lifeline.org.au"
DEFAULT_CSV = "paths.csv"


class ArticleNodeIdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.node_id: Optional[str] = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if self.node_id is not None:
            return
        if tag.lower() != "article":
            return
        attr_map = {k: v for k, v in attrs}
        node_id = attr_map.get("data-history-node-id")
        if node_id:
            self.node_id = node_id.strip()


def fetch_node_id(url: str, timeout: float = 20.0) -> Optional[str]:
    req = Request(
        url,
        headers={
            "User-Agent": "toolkit-tags-nodeid-fetch/1.0 (+https://www.lifeline.org.au)"
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        content_type = resp.headers.get("Content-Type", "")
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()
        html = resp.read().decode(charset, errors="replace")

    parser = ArticleNodeIdParser()
    parser.feed(html)
    return parser.node_id


def normalize_url(base_url: str, drupal_path: str) -> str:
    if drupal_path.startswith("http://") or drupal_path.startswith("https://"):
        return drupal_path
    return f"{base_url.rstrip('/')}/{drupal_path.lstrip('/')}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add Drupal node IDs to paths.csv by scraping lifeline.org.au"
    )
    parser.add_argument("--csv", default=DEFAULT_CSV, help="CSV file to update")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL for Drupal paths",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests (seconds)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip rows that already have a node id",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print("CSV is empty.", file=sys.stderr)
        return 1

    header = rows[0]
    node_col_name = "node-id"
    edit_col_name = "edit-link"
    if node_col_name in header:
        node_col_idx = header.index(node_col_name)
    else:
        header.append(node_col_name)
        node_col_idx = len(header) - 1

    if edit_col_name in header:
        edit_col_idx = header.index(edit_col_name)
    else:
        header.append(edit_col_name)
        edit_col_idx = len(header) - 1

    updated_rows = [header]
    total = len(rows) - 1

    for i, row in enumerate(rows[1:], start=1):
        # Ensure row has enough columns
        while len(row) <= max(node_col_idx, edit_col_idx):
            row.append("")

        drupal_path = row[0].strip() if row else ""
        existing = row[node_col_idx].strip()

        if args.skip_existing and existing:
            print(f"[{i}/{total}] skip (already has node-id): {drupal_path}")
            updated_rows.append(row)
            continue

        if not drupal_path:
            print(f"[{i}/{total}] empty drupal path, leaving blank")
            updated_rows.append(row)
            continue

        url = normalize_url(args.base_url, drupal_path)

        try:
            node_id = fetch_node_id(url)
            if node_id:
                row[node_col_idx] = node_id
                row[edit_col_idx] = f"{args.base_url.rstrip('/')}/node/{node_id}/edit"
                print(f"[{i}/{total}] {drupal_path} -> {node_id}")
            else:
                row[node_col_idx] = ""
                row[edit_col_idx] = ""
                print(f"[{i}/{total}] {drupal_path} -> not found")
        except Exception as exc:
            row[node_col_idx] = ""
            row[edit_col_idx] = ""
            print(f"[{i}/{total}] {drupal_path} -> error: {exc}")

        updated_rows.append(row)
        if args.delay > 0:
            time.sleep(args.delay)

    tmp_path = csv_path.with_suffix(csv_path.suffix + ".tmp")
    with tmp_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(updated_rows)

    tmp_path.replace(csv_path)
    print(f"Updated: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

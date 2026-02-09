"""
Prepare Sanity metadata for Drupal field population.

Reads the Sanity articles_metadata.json export, classifies each article's tags
into the correct Drupal taxonomy fields using a label-based mapping, and outputs
a page_fields.json file ready for the browser automation script.
"""

import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Tag label -> Drupal field mapping
#
# Each Sanity tag category maps to one Drupal field.  We build a flat dict of
# tag_label -> drupal_field_name so we can classify every tag in an article's
# tags[] array.
# ---------------------------------------------------------------------------

TAG_LABEL_TO_FIELD: dict[str, str] = {}

_CATEGORY_MAP: dict[str, list[str]] = {
    # Sanity category "Topics" -> Drupal field_topics
    "field_topics": [
        "Eating and body image",
        "Relationships",
        "Panic attacks",
        "Natural disasters",
        "Stress",
        "Self-harm",
        "Suicide",
        "Psychosis",
        "Grief",
        "Gambling",
        "Domestic and family violence",
        "Financial stress",
        "Trauma",
        "Loneliness",
        "Depression",
        "Substance Misuse",
        "Anxiety",
    ],
    # Sanity "Listen, watch, or read" -> Drupal field_media_type
    # NOTE: Sanity "Media Type" category (Audio/Graphic/Video) does NOT match
    # Drupal's media_type checkboxes which are Listen/Read/Watch only.
    "field_media_type": [
        "Read",
        "Watch",
        "Listen",
    ],
    # Sanity "For others content" -> Drupal field_audience
    "field_audience": [
        "Carer Stories",
        "For Others Page",
        "Friends Family",
    ],
    # Sanity "Quiz - Manage Now or Help Long Term" -> Drupal field_quiz_question_2
    "field_quiz_question_2": [
        "Long-term help",
        "Short-term help",
    ],
    # Sanity "Help right now or long term" -> Drupal field_timeframe
    "field_timeframe": [
        "Long term",
        "Right now",
    ],
    # Sanity "Content Type" -> Drupal field_support_toolkit_type
    "field_support_toolkit_type": [
        "Technique or Strategy",
        "Support Service",
        "Support Guide",
        "Real Story",
        "Tool or App",
    ],
    # Sanity "Type" -> Drupal field_tools_apps_type
    "field_tools_apps_type": [
        "Online Program",
        "Book",
        "Website",
        "App",
    ],
    # Sanity "Quiz - Something Else" -> Drupal field_quiz_question_1
    # (This is a term within the quiz_question_1 vocabulary, not a separate field)
    "field_quiz_question_1": [
        "Other topics",
    ],
    # Sanity "Quiz - Understanding" -> kept as separate field
    "field_quiz_understanding": [
        "Understanding",
    ],
    # Sanity "Cost" -> Drupal field_cost
    "field_cost": [
        "Low cost",
        "Free",
    ],
    # Sanity "Access Options" -> Drupal field_access_options
    "field_access_options": [
        "Online",
        "Phone",
        "Counselling",
        "Text",
        "Forum",
        "Peer Support",
        "Crisis",
        "In Person",
    ],
    # Sanity "State" -> Drupal field_state
    "field_state": [
        "National",
        "NT",
        "ACT",
        "SA",
        "TAS",
        "VIC",
        "WA",
        "QLD",
        "NSW",
    ],
    # Sanity "Priority" -> Drupal field_quiz_priority
    "field_quiz_priority": [
        "Priority 3",
        "Priority 2",
        "Priority 1",
    ],
}

# Build the flat lookup
for field_name, labels in _CATEGORY_MAP.items():
    for label in labels:
        if label in TAG_LABEL_TO_FIELD:
            print(
                f"WARNING: Duplicate tag label '{label}' - already mapped to "
                f"'{TAG_LABEL_TO_FIELD[label]}', skipping mapping to '{field_name}'",
                file=sys.stderr,
            )
            continue
        TAG_LABEL_TO_FIELD[label] = field_name

# Tags that exist in Sanity but have no Drupal equivalent (ignore silently)
IGNORED_TAGS = {"Audio", "Graphic", "Video"}

# ---------------------------------------------------------------------------
# 1b. Sanity label -> Drupal label translation
#
# Some Sanity tag labels don't match the Drupal taxonomy term names exactly.
# This dict maps Sanity labels to the correct Drupal term names.
# ---------------------------------------------------------------------------

LABEL_TRANSLATION: dict[str, str] = {
    # field_support_toolkit_type
    "Technique or Strategy": "Techniques & Guides",
    "Tool or App": "Tools & Apps",
    # field_timeframe
    "Right now": "Help right now",
    "Long term": "Long term help",
    # field_quiz_question_2
    "Short-term help": "Try something to help me manage now",
    "Long-term help": "Strategies to help me long term",
    # field_quiz_question_1
    "Other topics": "I'm feeling something else",
    # field_audience
    "For Others Page": "For Others",
    "Friends Family": "For Friends & Family",
    # field_topics
    "Grief": "Grief & loss",
    "Gambling": "Problem gambling",
    # field_access_options
    "Online": "Online Chat",
}


def translate_label(label: str) -> str:
    """Translate a Sanity label to its Drupal equivalent."""
    return LABEL_TRANSLATION.get(label, label)


# ---------------------------------------------------------------------------
# 2. File paths
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).parent
SANITY_EXPORT = Path("/home/aido/projects/lla-website/sanity/output/articles_metadata.json")
PATHS_CSV = PROJECT_DIR / "paths.csv"
OUTPUT_FILE = PROJECT_DIR / "page_fields.json"


# ---------------------------------------------------------------------------
# 3. Load paths.csv -> dict mapping sanity_path (no leading /) to drupal_path
# ---------------------------------------------------------------------------

def load_path_mapping() -> dict[str, str]:
    """Return {sanity_path: drupal_path} from paths.csv."""
    mapping: dict[str, str] = {}
    with open(PATHS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sanity = row["sanity-path"].strip()
            drupal = row["drupal-path"].strip()
            # Skip entries where the sanity path is a full URL (not a relative path)
            if sanity.startswith("http"):
                continue
            mapping[sanity] = drupal
    return mapping


# ---------------------------------------------------------------------------
# 4. Process one article -> field values
# ---------------------------------------------------------------------------

def classify_article(article: dict) -> dict[str, list[str]]:
    """
    Given a Sanity article object, return a dict of
    {drupal_field_name: [term_label, ...]} for all tags and feelings.
    """
    fields: dict[str, list[str]] = {}

    # --- Process tags[] ---
    tags = article.get("tags") or []
    unmapped_tags: list[str] = []
    for tag in tags:
        label = (tag.get("label") or "").strip()
        if not label:
            continue
        field = TAG_LABEL_TO_FIELD.get(label)
        if field:
            # Translate the label to Drupal's term name
            drupal_label = translate_label(label)
            fields.setdefault(field, []).append(drupal_label)
        elif label not in IGNORED_TAGS:
            unmapped_tags.append(label)

    if unmapped_tags:
        print(
            f"  WARNING: Unmapped tags for '{article.get('title', '?')}': {unmapped_tags}",
            file=sys.stderr,
        )

    # --- Process feelings[] ---
    feelings = article.get("feelings") or []
    for feeling in feelings:
        # Feelings can be {label, value} objects or plain strings
        if isinstance(feeling, dict):
            label = (feeling.get("label") or "").strip()
        elif isinstance(feeling, str):
            label = feeling.strip()
        else:
            continue
        if label:
            fields.setdefault("field_feelings", []).append(label)

    return fields


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def main() -> None:
    # Load Sanity export
    print(f"Loading Sanity export from {SANITY_EXPORT} ...")
    with open(SANITY_EXPORT, encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles", [])
    print(f"  Found {len(articles)} articles")

    # Load path mapping
    print(f"Loading path mapping from {PATHS_CSV} ...")
    path_map = load_path_mapping()
    print(f"  Found {len(path_map)} path mappings")

    # Process each article
    results: list[dict] = []
    matched = 0
    unmatched_paths: list[str] = []

    for article in articles:
        sanity_path_raw = article.get("path", "")
        # Strip leading slash to match paths.csv format
        sanity_path = sanity_path_raw.lstrip("/")

        drupal_path = path_map.get(sanity_path)
        if not drupal_path:
            unmatched_paths.append(sanity_path)
            continue

        matched += 1
        fields = classify_article(article)

        # Only include if there are fields to populate
        if fields:
            results.append({
                "drupal_path": drupal_path,
                "sanity_path": sanity_path,
                "title": article.get("title") or article.get("name") or "",
                "fields": fields,
            })

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Summary
    print(f"\n--- Summary ---")
    print(f"  Articles in export: {len(articles)}")
    print(f"  Matched to Drupal paths: {matched}")
    print(f"  With populatable fields: {len(results)}")
    print(f"  Unmatched (no Drupal path): {len(unmatched_paths)}")

    if unmatched_paths:
        print(f"\n  Unmatched Sanity paths:")
        for p in sorted(unmatched_paths):
            print(f"    - {p}")

    # Field stats
    field_counts: dict[str, int] = {}
    for r in results:
        for field_name in r["fields"]:
            field_counts[field_name] = field_counts.get(field_name, 0) + 1
    print(f"\n  Field coverage (how many pages have each field):")
    for field, count in sorted(field_counts.items(), key=lambda x: -x[1]):
        print(f"    {field}: {count} pages")

    print(f"\nOutput written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

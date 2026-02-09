# Plan — Next Steps

## Where we are

- `prepare_data.py` — done, generates `page_fields.json` (164 pages)
- `fill_fields.js` — done, tested on UAT for one page (Sleep and mental health)
- Label translations — all 12 confirmed mismatches handled
- UAT single-page test — all fields filled correctly, **not yet saved**

---

## Remaining steps

### Step 1: Save the UAT test page
- Review the filled form on node 374 (Sleep and mental health)
- Save and verify no validation errors
- Check the saved page to confirm all values persisted

### Step 2: Create the automation runner
Build a script (Python or JS) that drives the page-by-page workflow:

1. **Look up Drupal node ID** for each page in `page_fields.json`
   - Option A: Use Drupal's admin content list (`/admin/content?title=...`) to find node IDs
   - Option B: Navigate to the page by alias and extract the node ID from the edit link
   - Option C: Use the Drupal JSON:API or REST endpoint to resolve path → node ID
2. **Navigate** to `/node/{nid}/edit` (without credentials in URL)
3. **Click the Categories tab**
4. **Inject the fill script** via `javascript:void(...)` URL
5. **Verify** all fields were set (read back values)
6. **Save** the form
7. **Log** success/failure for each page

The runner should:
- Process pages sequentially (to avoid overwhelming the server)
- Skip pages that already have values populated (to allow re-running safely)
- Log results to a CSV/JSON file for audit trail
- Support a `--dry-run` flag that fills but doesn't save

### Step 3: Test on 3–4 UAT pages of different types
Test with one page of each Support Toolkit Type to exercise all widget types:
- **Techniques & Guides** — already tested (Sleep and mental health)
- **Real Story** — has media_type checkboxes, topics, support_toolkit_type
- **Support Service** — has access_options, cost, state checkboxes
- **Tools & Apps** — has tools_apps_type checkboxes, cost

### Step 4: Run all 164 pages on UAT
- Execute the runner against UAT
- Review the log for any failures
- Spot-check 10–15 pages manually

### Step 5: Run on production
- Same runner, pointed at `PROD_URL`
- Ensure you're logged in with the right credentials
- Navigate to prod without credentials in URL (cache auth first)

---

## Known limitations / manual work needed

| Issue | Pages affected | Action |
|---|---|---|
| `field_feelings` vocabulary is empty | 3 pages | Create terms manually in Drupal, then fill |
| `field_timeframe` is single-select | 118 pages | Only first value set; review if second value matters |
| 5 Sanity stories have no Drupal path | 5 pages | May need paths.csv update or manual creation |
| Fields not from Sanity (manual later) | All pages | Website Section, Interest Group, Experiences, Wellbeing Stage, Quiz Question 1 |

---

## Key files

| File | Purpose |
|---|---|
| `prepare_data.py` | Transforms Sanity export → `page_fields.json` |
| `fill_fields.js` | Injectable browser script for filling Drupal forms |
| `page_fields.json` | Generated data: 164 pages with field values |
| `paths.csv` | Sanity path ↔ Drupal path mapping |
| `.env` | UAT/prod URLs and HTTP basic auth credentials |
| `progress.md` | Detailed notes on discoveries and gotchas |

---

## How to resume

1. Read `progress.md` for all the non-obvious gotchas
2. Read `prepare_data.py` (especially `LABEL_TRANSLATION` dict) for the full mapping
3. Read `fill_fields.js` for the browser-side fill logic
4. The UAT browser session should still be logged in — check by navigating to the UAT URL
5. If auth expired, navigate once with credentials: `https://admin:uvZ%2BUH7e10VIRsFeNQZHGA%3D%3D@lla-drupal-app-uat.lifeline.org.au/` then immediately navigate WITHOUT credentials for all subsequent pages

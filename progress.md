# Progress — Drupal Metadata Migration

## What's been built

### `prepare_data.py`
Reads the Sanity export (`articles_metadata.json`), classifies each article's tags into the correct Drupal fields using a label-based mapping, translates mismatched labels, and outputs `page_fields.json` (164 pages with populatable fields).

### `fill_fields.js`
Browser-injectable script that fills Drupal's node edit form. Handles three widget types: autocomplete (entity reference), select dropdowns, and checkboxes. Uses Drupal's own autocomplete API to resolve term names to `"Term name (TID)"` format.

### `page_fields.json`
Generated output — one entry per page with `drupal_path`, `sanity_path`, `title`, and a `fields` object mapping Drupal field names to arrays of term labels.

---

## Non-obvious things learned

### 1. HTTP basic auth in the URL breaks `fetch()`
When you navigate to `https://user:pass@example.com/path`, the browser stores the credentials in the page's origin. Any subsequent `fetch()` call with a relative URL inherits those credentials, and **modern browsers block this** with: `"Request cannot be constructed from a URL that includes credentials"`. **Fix**: navigate with credentials once (to cache them), then navigate to the same page WITHOUT credentials in the URL before running any JavaScript that uses `fetch()`.

### 2. Drupal autocomplete API returns HTML-encoded labels
The autocomplete endpoint (e.g. `/entity_reference_autocomplete/taxonomy_term/...`) returns labels with HTML entities — `&` becomes `&amp;` in the JSON label field. You must **decode HTML entities** before comparing labels. A simple browser-based decoder works:
```js
function htmlDecode(str) {
  const txt = document.createElement("textarea");
  txt.innerHTML = str;
  return txt.value;
}
```

### 3. Autocomplete URL already contains query parameters
The `data-autocomplete-path` attribute on Drupal autocomplete inputs already includes `?entity_type=node&entity_id=374`. You must append the search term with `&q=term`, **not** `?q=term`. Check: `path.includes('?') ? '&' : '?'`.

### 4. Sanity → Drupal label mismatches (complete list)
These are the confirmed translations needed:

| Sanity label | Drupal term | Field |
|---|---|---|
| Technique or Strategy | Techniques & Guides | `field_support_toolkit_type` |
| Tool or App | Tools & Apps | `field_support_toolkit_type` |
| Right now | Help right now | `field_timeframe` |
| Long term | Long term help | `field_timeframe` |
| Short-term help | Try something to help me manage now | `field_quiz_question_2` |
| Long-term help | Strategies to help me long term | `field_quiz_question_2` |
| Other topics | Something Else | `field_quiz_something_else` |
| For Others Page | For Others | `field_audience` |
| Friends Family | For Friends & Family | `field_audience` |
| Grief | Grief & loss | `field_topics` |
| Gambling | Problem gambling | `field_topics` |
| Online | Online Chat | `field_access_options` |

### 5. `field_timeframe` is single-select
Despite the data having multiple values (e.g. both "Help right now" and "Long term help"), the Drupal `field_timeframe` is a regular `<select>` (not `<select multiple>`). Only the **first value** can be set. The script handles this gracefully.

### 6. `field_feelings` vocabulary is empty in Drupal
The feelings taxonomy has **no terms** yet. The autocomplete returns empty for every query. Only 3 pages have feelings data, so these need manual handling after terms are created.

### 7. Sanity tags with no Drupal equivalent
"Audio", "Graphic", "Video" from Sanity's media type category have no matching Drupal checkbox. Drupal's `field_media_type` only has: Listen, Read, Watch. These Sanity tags are silently ignored.

### 8. Form structure — Categories tab has collapsed sub-groups
The edit form's "Categories" tab contains collapsible `<details>` sub-groups: "Techniques & Guides", "Tools & Apps", "Real Story", "Support Service". Fields inside collapsed groups (like `field_timeframe`, `field_access_options`) are still in the DOM and can be filled via JavaScript — no need to expand them first.

### 9. "Add another item" AJAX needs polling, not fixed waits
Drupal's multi-value fields use AJAX to add new rows when clicking "Add another item". A fixed `setTimeout` is unreliable — instead, **poll** for the new input element every 500ms with a 10-second timeout.

### 10. Drupal form field widget types (confirmed from live form)

| Widget | Fields |
|---|---|
| `entity_reference_autocomplete` | topics, audience, feelings, access_options, quiz_priority, quiz_question_1, quiz_question_2, quiz_understanding, quiz_something_else, helps_with, recommended_topics |
| `options_select` | support_toolkit_type, cost, timeframe |
| `options_buttons` (checkboxes) | media_type, state, tools_apps_type |

### 11. Checkbox value-to-label mapping (from live form)

**media_type**: Listen=132, Read=131, Watch=130
**tools_apps_type**: App=155, Book=153, Online Program=152, Website=154
**state**: ACT=136, National=140, NSW=144, NT=142, QLD=143, SA=137, TAS=138, VIC=139, WA=141

### 12. 5 Sanity articles have no Drupal path match
These stories don't exist in `paths.csv`:
- cristinas-story, emily-and-ians-story, kirans-story, stellas-story, wills-story

---

## Test results (UAT — "Sleep and mental health", node 374)

All fields successfully filled:
- ✅ `field_support_toolkit_type` = "Techniques & Guides" (select)
- ✅ `field_timeframe` = "Help right now" (select, first value only)
- ✅ `field_topics` = 7 values including "Grief & loss" (autocomplete + Add another item AJAX)
- ✅ `field_quiz_question_2` = "Try something to help me manage now" (autocomplete)
- ✅ `field_quiz_something_else` = "Something Else" (autocomplete)

**Not yet saved** — waiting for approval before committing changes on UAT.

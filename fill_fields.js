/**
 * fill_fields.js — Drupal Support Toolkit Page field filler
 *
 * Paste this into the browser console on a Drupal node edit page.
 * It fills taxonomy fields using autocomplete API lookups (for entity
 * reference fields), select changes, and checkbox clicks.
 *
 * DOES NOT auto-save. Review the form before saving manually.
 *
 * Usage:
 *   1. Navigate to a node edit page (e.g. /node/123/edit)
 *   2. Open browser console
 *   3. Paste this entire script
 *   4. Call: await fillPageFields({ field_topics: ["Anxiety"], ... })
 */

(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Configuration: which fields use which widget type
  // -----------------------------------------------------------------------
  const AUTOCOMPLETE_FIELDS = new Set([
    "field_topics",
    "field_audience",
    "field_feelings",
    "field_access_options",
    "field_quiz_priority",
    "field_quiz_question_1",
    "field_quiz_question_2",
    "field_quiz_understanding",
    "field_helps_with",
    "field_recommended_topics",
  ]);

  const SELECT_FIELDS = new Set([
    "field_cost",
    "field_support_toolkit_type",
    "field_timeframe",
  ]);

  const CHECKBOX_FIELDS = new Set([
    "field_media_type",
    "field_state",
    "field_tools_apps_type",
  ]);

  // -----------------------------------------------------------------------
  // Helpers
  // -----------------------------------------------------------------------

  function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Decode HTML entities (e.g. &amp; -> &, &lt; -> <) in a string.
   * Uses a temporary textarea element to leverage the browser's built-in decoder.
   */
  function htmlDecode(str) {
    const txt = document.createElement("textarea");
    txt.innerHTML = str;
    return txt.value;
  }

  function log(msg) {
    console.log(`%c[fill_fields] ${msg}`, "color: #2196F3; font-weight: bold");
  }

  function warn(msg) {
    console.warn(`[fill_fields] ${msg}`);
  }

  function error(msg) {
    console.error(`[fill_fields] ${msg}`);
  }

  /**
   * Wait for a condition to be true, checking every `interval` ms.
   * Rejects after `timeout` ms.
   */
  function waitFor(conditionFn, timeout = 5000, interval = 200) {
    return new Promise((resolve, reject) => {
      const start = Date.now();
      const check = () => {
        const result = conditionFn();
        if (result) {
          resolve(result);
        } else if (Date.now() - start > timeout) {
          reject(new Error("waitFor timed out"));
        } else {
          setTimeout(check, interval);
        }
      };
      check();
    });
  }

  // -----------------------------------------------------------------------
  // Autocomplete fields
  // -----------------------------------------------------------------------

  /**
   * Find the field wrapper element for a given field machine name.
   * Drupal uses class names like .field--name-field-topics
   * (with hyphens instead of underscores).
   */
  function getFieldWrapper(fieldName) {
    const cssFieldName = fieldName.replace(/_/g, "-");
    return document.querySelector(`.field--name-${cssFieldName}`);
  }

  /**
   * For an autocomplete input, fetch the autocomplete API to resolve
   * a term name to its "Term name (TID)" value.
   */
  async function resolveAutocompleteValue(input, termName) {
    const autocompletePath = input.getAttribute("data-autocomplete-path");
    if (!autocompletePath) {
      throw new Error(`No data-autocomplete-path on input ${input.name}`);
    }

    const sep = autocompletePath.includes("?") ? "&" : "?";
    const url = `${autocompletePath}${sep}q=${encodeURIComponent(termName)}`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Autocomplete fetch failed: ${response.status}`);
    }

    const results = await response.json();

    // Find exact match (case-insensitive, HTML-decoded)
    const termLower = termName.toLowerCase().trim();
    const match = results.find(
      (r) => htmlDecode(r.label).toLowerCase().trim() === termLower
    );
    if (match) {
      return match.value; // e.g. "Anxiety (42)"
    }

    // Partial match fallback
    const partial = results.find((r) =>
      htmlDecode(r.label).toLowerCase().includes(termName.toLowerCase())
    );
    if (partial) {
      warn(
        `No exact match for "${termName}", using partial: "${partial.label}"`
      );
      return partial.value;
    }

    warn(
      `No autocomplete match for "${termName}". Results: ${JSON.stringify(results.map((r) => r.label))}`
    );
    return null;
  }

  /**
   * Fill an autocomplete field with multiple values.
   */
  async function fillAutocompleteField(fieldName, values) {
    const wrapper = getFieldWrapper(fieldName);
    if (!wrapper) {
      error(`Field wrapper not found for ${fieldName}`);
      return;
    }

    for (let i = 0; i < values.length; i++) {
      const termName = values[i];

      // Find the current empty input (delta = i)
      let input = wrapper.querySelector(
        `input[name="${fieldName}[${i}][target_id]"]`
      );

      // If no input at this delta, we need to click "Add another item"
      if (!input) {
        const addMoreBtn = wrapper.querySelector(
          'input[type="submit"][value="Add another item"]'
        );
        if (!addMoreBtn) {
          error(`No "Add another item" button found for ${fieldName}`);
          return;
        }

        log(`  Clicking "Add another item" for ${fieldName}...`);
        addMoreBtn.dispatchEvent(new MouseEvent("mousedown", { bubbles: true }));
        addMoreBtn.click();

        // Wait for AJAX to add the new input
        try {
          await waitFor(
            () =>
              wrapper.querySelector(
                `input[name="${fieldName}[${i}][target_id]"]`
              ),
            10000
          );
        } catch {
          error(`Timed out waiting for new input row for ${fieldName}[${i}]`);
          return;
        }
        await sleep(300); // Extra settle time after AJAX

        input = wrapper.querySelector(
          `input[name="${fieldName}[${i}][target_id]"]`
        );
      }

      if (!input) {
        error(`Input not found for ${fieldName}[${i}]`);
        continue;
      }

      // Skip if already filled with the same value
      if (input.value && input.value.toLowerCase().includes(termName.toLowerCase())) {
        log(`  ${fieldName}[${i}] already has "${termName}", skipping`);
        continue;
      }

      // Resolve the term via autocomplete API
      const resolvedValue = await resolveAutocompleteValue(input, termName);
      if (!resolvedValue) {
        error(`  Could not resolve "${termName}" for ${fieldName}`);
        continue;
      }

      // Set the value
      input.value = resolvedValue;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));

      log(`  ${fieldName}[${i}] = "${resolvedValue}"`);
      await sleep(100);
    }
  }

  // -----------------------------------------------------------------------
  // Select fields (multi-select)
  // -----------------------------------------------------------------------

  async function fillSelectField(fieldName, values) {
    const wrapper = getFieldWrapper(fieldName);
    if (!wrapper) {
      error(`Field wrapper not found for ${fieldName}`);
      return;
    }

    const select = wrapper.querySelector("select");
    if (!select) {
      error(`<select> not found in ${fieldName}`);
      return;
    }

    const isMultiple = select.multiple;

    if (isMultiple) {
      // Deselect all first (for multi-select)
      for (const option of select.options) {
        option.selected = false;
      }
    }

    // For single-select, only use the first value and warn if more provided
    const effectiveValues = isMultiple ? values : values.slice(0, 1);
    if (!isMultiple && values.length > 1) {
      warn(`  ${fieldName}: single-select, using first value only ("${values[0]}"), skipping: ${JSON.stringify(values.slice(1))}`);
    }

    for (const termName of effectiveValues) {
      let matched = false;
      for (const option of select.options) {
        if (
          option.text.trim().toLowerCase() === termName.toLowerCase() ||
          option.value.toLowerCase() === termName.toLowerCase()
        ) {
          option.selected = true;
          select.value = option.value;
          matched = true;
          log(`  ${fieldName}: selected "${option.text.trim()}"`);
          break;
        }
      }
      if (!matched) {
        warn(`  ${fieldName}: no option matching "${termName}"`);
        // Log available options for debugging
        const available = Array.from(select.options).map(o => o.text.trim()).filter(t => t && t !== '- None -');
        warn(`  Available options: ${JSON.stringify(available)}`);
      }
    }

    // Trigger change event so Drupal knows the value changed
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // -----------------------------------------------------------------------
  // Checkbox/radio fields
  // -----------------------------------------------------------------------

  async function fillCheckboxField(fieldName, values) {
    const wrapper = getFieldWrapper(fieldName);
    if (!wrapper) {
      error(`Field wrapper not found for ${fieldName}`);
      return;
    }

    const checkboxes = wrapper.querySelectorAll(
      'input[type="checkbox"], input[type="radio"]'
    );

    if (checkboxes.length === 0) {
      error(`No checkboxes/radios found in ${fieldName}`);
      return;
    }

    for (const termName of values) {
      let matched = false;
      for (const cb of checkboxes) {
        // Match by the associated label text
        const label = wrapper.querySelector(`label[for="${cb.id}"]`);
        const labelText = label ? label.textContent.trim() : "";

        if (
          labelText.toLowerCase() === termName.toLowerCase() ||
          cb.value.toLowerCase() === termName.toLowerCase()
        ) {
          if (!cb.checked) {
            cb.click();
            log(`  ${fieldName}: checked "${labelText || cb.value}"`);
          } else {
            log(`  ${fieldName}: "${labelText || cb.value}" already checked`);
          }
          matched = true;
          break;
        }
      }
      if (!matched) {
        warn(`  ${fieldName}: no checkbox/radio matching "${termName}"`);
        // Log available options
        const available = Array.from(checkboxes).map(cb => {
          const label = wrapper.querySelector(`label[for="${cb.id}"]`);
          return label ? label.textContent.trim() : cb.value;
        });
        warn(`  Available options: ${JSON.stringify(available)}`);
      }
    }
  }

  // -----------------------------------------------------------------------
  // Main entry point
  // -----------------------------------------------------------------------

  /**
   * Fill all fields for a single page.
   *
   * @param {Object} fields - { field_topics: ["Anxiety", "Depression"], ... }
   */
  async function fillPageFields(fields) {
    log("Starting field fill...");
    const startTime = Date.now();

    for (const [fieldName, values] of Object.entries(fields)) {
      if (!values || values.length === 0) continue;

      log(`Filling ${fieldName} with ${values.length} value(s): ${JSON.stringify(values)}`);

      try {
        if (AUTOCOMPLETE_FIELDS.has(fieldName)) {
          await fillAutocompleteField(fieldName, values);
        } else if (SELECT_FIELDS.has(fieldName)) {
          await fillSelectField(fieldName, values);
        } else if (CHECKBOX_FIELDS.has(fieldName)) {
          await fillCheckboxField(fieldName, values);
        } else {
          warn(`Unknown field type for ${fieldName}, skipping`);
        }
      } catch (err) {
        error(`Error filling ${fieldName}: ${err.message}`);
      }

      await sleep(200);
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    log(`Done! Filled fields in ${elapsed}s. Review the form before saving.`);
  }

  // Expose globally so it can be called from the console
  window.fillPageFields = fillPageFields;

  log("Script loaded. Call: await fillPageFields({ field_topics: [...], ... })");
})();

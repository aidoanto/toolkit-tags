/**
 * get_edit_urls.js — Paste into the browser console on any Drupal page
 * (while logged in as admin) to fetch all support_toolkit_page node IDs
 * and generate a list of edit URLs matched to our page_fields.json data.
 *
 * Outputs a clickable list in the console and a copy-pasteable text block.
 *
 * Usage:
 *   1. Log into Drupal (prod or UAT)
 *   2. Open browser console
 *   3. Paste this entire script
 *   4. Wait for it to finish (it pages through JSONAPI results)
 *   5. Copy the output list of edit URLs
 */
(async function () {
  "use strict";

  console.log("%c[get_edit_urls] Fetching all support_toolkit_page nodes...", "color: #2196F3; font-weight: bold");

  const nodes = [];
  let url = "/jsonapi/node/support_toolkit_page?fields[node--support_toolkit_page]=title,path&page[limit]=50";

  while (url) {
    console.log(`  Fetching page... (${nodes.length} nodes so far)`);
    const response = await fetch(url);
    if (!response.ok) {
      console.error(`Fetch failed: ${response.status} ${response.statusText}`);
      break;
    }
    const data = await response.json();

    for (const item of data.data || []) {
      const nid = item.id; // UUID
      const drupalId = item.attributes?.drupal_internal__nid;
      const title = item.attributes?.title || "";
      const alias = item.attributes?.path?.alias || "";

      if (drupalId && alias) {
        nodes.push({
          nid: drupalId,
          title: title,
          alias: alias.replace(/^\//, ""), // strip leading slash
        });
      }
    }

    // Follow "next" link for pagination
    url = data.links?.next?.href || null;
    if (url) {
      // Make relative if it's absolute
      try {
        const parsed = new URL(url);
        url = parsed.pathname + parsed.search;
      } catch {
        // already relative
      }
    }
  }

  console.log(`%c[get_edit_urls] Found ${nodes.length} support_toolkit_page nodes`, "color: #4CAF50; font-weight: bold");

  // Build a lookup: alias -> nid
  const aliasToNid = {};
  for (const n of nodes) {
    aliasToNid[n.alias] = n.nid;
  }

  // Output: list of edit URLs
  const editUrls = nodes
    .sort((a, b) => a.alias.localeCompare(b.alias))
    .map(n => ({
      url: `/node/${n.nid}/edit`,
      title: n.title,
      alias: n.alias,
      nid: n.nid,
    }));

  // Print as a nice table
  console.table(editUrls.map(e => ({ title: e.title, edit_url: e.url, alias: e.alias })));

  // Also store globally for easy access
  window._editUrls = editUrls;
  window._aliasToNid = aliasToNid;

  // Generate copy-pasteable text
  const text = editUrls.map(e => `${e.url}\t${e.title}\t${e.alias}`).join("\n");
  console.log("%c[get_edit_urls] Stored in window._editUrls and window._aliasToNid", "color: #2196F3");
  console.log("%c[get_edit_urls] Copy-paste list:", "color: #2196F3");
  console.log(text);

  // Generate a simple helper to quickly open the next edit page
  console.log(`%c[get_edit_urls] Use window._editUrls to iterate. Example:`, "color: #888");
  console.log(`  window._editUrls[0].url  // first edit URL`);
  console.log(`  window._aliasToNid["get-help/support-toolkit/techniques-and-guides/sleep-and-mental-health"]  // lookup nid by alias`);
})();

---
name: vldb
description: Add a VLDB conference entry. Handles VLDB's monthly PVLDB submission cycle, including the abstract-on-the-25th-of-previous-month rule (Vol 20+) and DST-aware Pacific Time deadlines.
argument-hint: [VLDB Year, e.g. "2028"]
allowed-tools: WebFetch, Read, Write, Bash
---

# VLDB CFP

Add `conf/$ARGUMENTS/vldb.json` for **VLDB $ARGUMENTS**.

VLDB is monthly: PVLDB Volume N (= $ARGUMENTS − 2007) feeds VLDB $ARGUMENTS, with deadlines on the 1st of every month from **April ($ARGUMENTS − 1)** through **March ($ARGUMENTS)** at **5 PM Pacific Time**. The pipeline expands a single `first_deadline` template into 12 monthly entries — see [build.py](../../../build.py).

## Steps

1. **Check if the file already exists** and warn if so:

   !`ls conf/$ARGUMENTS/vldb.json 2>/dev/null && echo "EXISTS — will overwrite" || echo "new file"`

2. **Fetch venue + conference dates** from `https://vldb.org/$ARGUMENTS/`. Extract:
   - `venue`: "City, Country" (e.g. "Athens, Greece"; "Boston, MA, USA" for US)
   - `start` / `end`: YYYY-MM-DD

   If the page is not yet up, stop and tell the user.

3. **Confirm the submission cycle** by fetching `https://vldb.org/$ARGUMENTS/submission-guidelines.html` (or `call-for-research-track.html`). Sanity-check that deadlines are still:
   - 1st of each month, 5 PM Pacific
   - Abstract on the 25th of previous month (Vol 20+)
   - Notification on the 15th of the next month

   If any of these have changed for this year, surface the discrepancy and ask the user before continuing.

4. **Build the JSON** using this template — substituting `$ARGUMENTS`, the fetched venue/dates, and the Vol number:

   ```json
   {
     "title": "VLDB",
     "year": <year>,
     "venue": "<City, Country>",
     "start": "<YYYY-MM-DD>",
     "end": "<YYYY-MM-DD>",
     "areas": ["DB"],
     "cfp_link": "https://vldb.org/<year>/call-for-research-track.html",
     "frequency": "monthly",
     "first_deadline": {
       "season": "April",
       "paper_deadline": "<year-1>-04-01 17:00:00",
       "abstract_deadline": <"<year-1>-03-25 17:00:00" if Vol >= 20 else null>,
       "author_notification": "<year-1>-05-15 00:00:00",
       "named_timezone": "PT"
     }
   }
   ```

   **Vol-specific differences:**
   - Vol ≤ 19 (VLDB ≤ 2026): `abstract_deadline: null`. No separate abstract.
   - Vol ≥ 20 (VLDB ≥ 2027): abstract on the 25th of the previous month, same 5 PM PT.

5. **Show the JSON** to the user. Confirm before writing.

6. **Save** to `conf/$ARGUMENTS/vldb.json`. Create the year directory if needed.

7. **Rebuild and spot-check**:

   !`python3 build.py`

   Then verify a DST-boundary entry looks right (e.g. November cycle: paper in PST, abstract in PDT).

## Schema notes

- `named_timezone: "PT"` triggers DST-aware per-field expansion in `build.py`. Each of `paper_deadline`, `abstract_deadline`, and `author_notification` is resolved at its own local datetime, so the November cycle correctly stores paper-in-PST + abstract-in-PDT even though they share an entry.
- Output `db.json` will normalize everything to `timezone: "UTC+0"` — that's expected; the frontend renders in viewer-local time via `toLocaleString`.
- Do NOT set both `timezone` and `named_timezone` — `build.py` errors out.

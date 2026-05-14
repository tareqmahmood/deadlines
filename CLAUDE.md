# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Build: `python3 build.py` — regenerates `public/db.json` and all HTML pages from `templates/` into `public/`.
- Serve locally: `python3 -m http.server -d public` (then open `index.html`).
- Add a conference: use the `/cfp` skill (e.g. `/cfp NeurIPS 2027`) — it searches the web for the CFP, extracts deadlines, and writes a new file under `conf/<year>/`.
- Add a VLDB year: use the dedicated `/vldb` skill (e.g. `/vldb 2028`) — it knows the PVLDB monthly cycle and Vol 20+ abstract rule.

There is no lint or test suite. `build.py` is the only build step; rerun it after editing any JSON or template.

## Architecture

This is a static site. The pipeline is **JSON → build.py → static `public/`**, served as-is by GitHub Pages.

**Source of truth — `conf/<year>/<title>.json`.** One file per conference per year. Schema is documented in the [README](README.md) and enforced by the [/cfp](.claude/skills/cfp/SKILL.md) and [/vldb](.claude/skills/vldb/SKILL.md) skills. Use `null` (not empty string) for unknown dates. `timezone` strings like `"UTC-12"`, `"UTC+0"` are parsed by [script.js](public/script.js) — keep that exact format.

**Rolling/monthly venues** (VLDB) use `frequency: "monthly"` with a single `first_deadline` template instead of a `deadlines` array. The template's `timezone` is either a fixed offset (`"UTC-8"`) OR a `named_timezone` (`"PT"`, `"ET"`, etc., or full IANA like `"America/Los_Angeles"`) for DST-aware resolution — exactly one, never both. `build.py` enforces this and errors out if violated.

**Build step — [build.py](build.py).** Three responsibilities:

1. Aggregates all `conf/<year>/*.json` for the current year and beyond into a single `public/db.json` (the only data file the frontend fetches). Adds derived `id` and `fileId` fields.
2. **Expands monthly venues.** For `frequency: "monthly"` conferences, `expand_monthly` shifts each field of `first_deadline` by `i` months (`i = 0..11`) — cross-month offsets like "abstract on the 25th of the previous month" are preserved. When `named_timezone` is set, each field is resolved at its own local datetime so paper/abstract/notification on different sides of a DST boundary still produce correct UTC instants; output is normalized to `timezone: "UTC+0"`.
3. **Auto-estimates missing future conferences.** For any conference present in `conf/<prev_year>/` but absent from the latest year in the conf tree, it creates a synthetic entry with all dates shifted +1 year, `is_estimated: true`, `venue: "TBD"`, blank CFP link. Skipped for monthly venues (their CFPs are not auto-estimable). The frontend renders these with an "ESTIMATED" badge and disables internal links. This is why deleting an old-year file silently removes a placeholder from the current view.
4. Renders HTML from `templates/`. Templates use a homegrown placeholder system — `{{TITLE}}`, `{{CONTENT}}`, `{{ACTIVE_<page>}}` — and HTML-comment frontmatter (`<!-- title: ... -->`, `<!-- active: ... -->`) for per-page config. [templates/base.html](templates/base.html) is the shell; every other template is inlined into `{{CONTENT}}`. The `active_pages` list in `build.py` controls which `{{ACTIVE_*}}` placeholders exist — keep templates and that list in sync when adding a page.

**Generated files are gitignored** (`public/db.json`, `public/*.html`). Don't commit them. Source HTML lives in `templates/`; `public/script.js` and `public/style.css` are the only hand-edited files in `public/`.

**Frontend — [public/script.js](public/script.js).** Single-file vanilla JS, no framework. `loadData()` does a cache-first fetch of `db.json` from `localStorage`, then re-renders if the network response differs. Page is dispatched off `window.location.pathname` in `renderCurrentPage()`. Deadlines flatten into `allDeadlines` (one entry per `deadlines[]` season), sorted by paper deadline — most rendering iterates this flat list rather than `conferences`.

**Deploy — [.github/workflows/deploy.yml](.github/workflows/deploy.yml).** On push to `main`: runs `build.py`, minifies JS/CSS/HTML, publishes `public/` to the `gh-pages` branch. No manual deploy step.

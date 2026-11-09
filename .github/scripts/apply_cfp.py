#!/usr/bin/env python3
"""Apply CFP data extracted by the coding agent.

The agent does ONLY the non-deterministic part: read each CFP page and emit raw
fields into `_extracted.json`. Everything here is deterministic — validate each
entry against the on-disk schema, refuse malformed or duplicate ones, and write
the good ones to conf/<year>/<title>.json. Nothing is trusted blindly.

Input file (`_extracted.json`) is a JSON array of objects:
  {"status": "added",   "data": { <full conference object> }}
  {"status": "skipped", "conference": "fast 2027", "reason": "CFP not announced"}

Exit code is non-zero only on a hard error (bad input file). Per-entry
validation failures are reported and skipped so one bad scrape can't sink the run.
"""
import json
import os
import re
import sys

AREAS = {"SYS", "ML", "DB"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
TZ_OFFSET_RE = re.compile(r"^UTC[+-]\d{1,2}$")
TZ_NAMED_RE = re.compile(r"^[A-Za-z][A-Za-z/_]+$")  # "PT", "America/Los_Angeles"


def err(msg):
    print(f"  ✗ {msg}")


def validate(data):
    """Return a list of problems (empty == valid)."""
    problems = []

    def need(key, types):
        if key not in data:
            problems.append(f"missing '{key}'")
        elif not isinstance(data[key], types):
            problems.append(f"'{key}' has wrong type")

    need("title", str)
    need("year", int)
    need("venue", str)
    need("cfp_link", str)
    need("areas", list)
    need("deadlines", list)

    for key in ("start", "end"):
        v = data.get(key)
        if v is not None and not (isinstance(v, str) and DATE_RE.match(v)):
            problems.append(f"'{key}' must be YYYY-MM-DD or null")

    if isinstance(data.get("areas"), list):
        bad = [a for a in data["areas"] if a not in AREAS]
        if bad:
            problems.append(f"invalid areas {bad}; allowed {sorted(AREAS)}")

    dls = data.get("deadlines")
    if isinstance(dls, list):
        if not dls:
            problems.append("'deadlines' is empty")
        for i, d in enumerate(dls):
            if not isinstance(d, dict):
                problems.append(f"deadline[{i}] not an object")
                continue
            if "season" in d and not (d["season"] is None or isinstance(d["season"], str)):
                problems.append(f"deadline[{i}].season must be string or null")
            for f in ("paper_deadline", "abstract_deadline", "author_notification"):
                v = d.get(f)
                if v is not None and not (isinstance(v, str) and DATETIME_RE.match(v)):
                    problems.append(f"deadline[{i}].{f} must be 'YYYY-MM-DD HH:MM:SS' or null")
            tz = d.get("timezone")
            if not (isinstance(tz, str) and (TZ_OFFSET_RE.match(tz) or TZ_NAMED_RE.match(tz))):
                problems.append(f"deadline[{i}].timezone invalid: {tz!r}")
            if d.get("paper_deadline") is None and d.get("abstract_deadline") is None:
                problems.append(f"deadline[{i}] has neither paper nor abstract date")
    return problems


# Canonical field order for stable, review-friendly diffs.
TOP_ORDER = ["title", "year", "venue", "start", "end", "areas", "cfp_link", "deadlines"]
DL_ORDER = ["season", "abstract_deadline", "paper_deadline", "author_notification", "timezone"]


def ordered(data):
    out = {k: data[k] for k in TOP_ORDER if k in data}
    out["deadlines"] = [
        {k: d[k] for k in DL_ORDER if k in d} for d in data["deadlines"]
    ]
    return out


def main():
    path = "_extracted.json"
    if not os.path.exists(path):
        print("No _extracted.json — agent added nothing. Nothing to do.")
        return 0

    try:
        entries = json.load(open(path))
        assert isinstance(entries, list)
    except Exception as e:
        print(f"::error::Could not parse {path}: {e}")
        return 1

    added, skipped, rejected = [], [], []

    for entry in entries:
        status = (entry or {}).get("status")
        if status == "skipped":
            skipped.append((entry.get("conference", "?"), entry.get("reason", "")))
            continue
        if status != "added":
            rejected.append((str(entry)[:60], "unknown status"))
            continue

        data = entry.get("data") or {}
        label = f"{data.get('title', '?')} {data.get('year', '?')}"

        if str(data.get("title", "")).lower() == "vldb":
            skipped.append((label, "VLDB is monthly — add manually via /vldb"))
            continue

        problems = validate(data)
        if problems:
            rejected.append((label, "; ".join(problems)))
            continue

        year = data["year"]
        fname = re.sub(r"[^a-z0-9]+", "", data["title"].lower())
        dest = os.path.join("conf", str(year), f"{fname}.json")
        if os.path.exists(dest):
            skipped.append((label, f"{dest} already exists"))
            continue

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w") as f:
            json.dump(ordered(data), f, indent=2)
            f.write("\n")
        added.append((label, dest))

    # Report
    print(f"\nAdded {len(added)}, skipped {len(skipped)}, rejected {len(rejected)}\n")
    for label, dest in added:
        print(f"  ✓ {label} -> {dest}")
    for label, reason in skipped:
        print(f"  – {label}: {reason}")
    for label, reason in rejected:
        err(f"{label}: {reason}")

    # Optional GitHub step summary
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as s:
            s.write(f"### Weekly CFP update\n\n")
            s.write(f"- **Added:** {len(added)}\n- **Skipped:** {len(skipped)}"
                    f"\n- **Rejected:** {len(rejected)}\n\n")
            for label, dest in added:
                s.write(f"- ✅ `{label}` → `{dest}`\n")
            for label, reason in skipped:
                s.write(f"- ⏭️ `{label}` — {reason}\n")
            for label, reason in rejected:
                s.write(f"- ❌ `{label}` — {reason}\n")

    # count added for the workflow (controls whether a PR is opened)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as o:
            o.write(f"added={len(added)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

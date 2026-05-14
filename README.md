# Conference Deadline Tracker

A simple, minimalistic, mobile-friendly website to track conference deadlines.

## Features
- **Deadlines View**: Countdown timers for upcoming deadlines.
- **Calendar View**: Monthly calendar showing deadlines and conference dates.
- **Conference Details**: Specific information for each conference.
- **Timezone Support**: Automatically detects user's timezone.
- **Dark/Light Mode**: Toggle between themes.
- **Google Calendar Integration**: Add deadlines to your calendar.

## How to Add a Conference

### Using Claude Code
Run the `/cfp` skill in Claude Code:
```
/cfp NeurIPS 2027
```
It will search the web for the CFP, extract deadlines, show you the result, and save it to the right `conf/` folder after confirmation.

### Manually
1. Create a new JSON file in `conf/<year>/<conference>.json`.
2. Use the following structure:
   ```json
   {
     "title": "ICML",
     "year": 2026,
     "venue": "Seoul, South Korea",
     "start": "2026-07-07",
     "end": "2026-07-12",
     "areas": ["ML"],
     "cfp_link": "https://icml.cc/Conferences/2026/CallForPapers",
     "deadlines": [
       {
         "season": null,
         "paper_deadline": "2026-01-29 12:00:00",
         "abstract_deadline": "2026-01-24 12:00:00",
         "author_notification": "2026-05-10 12:00:00",
         "timezone": "UTC+0"
       }
     ]
   }
   ```
3. Commit and push. The GitHub Action will automatically rebuild the index.

#### Rolling/monthly venues (e.g. VLDB)
For venues with a deadline every month, set `"frequency": "monthly"` and provide a single template object as `first_deadline` instead of `deadlines`. `build.py` shifts each field by `i` months for `i = 0..11`, so cross-month offsets (e.g. abstract on the 25th of the previous month) are preserved. The homepage shows only the next two so it doesn't crowd out other deadlines.

Use exactly one of these on the template:
- `"timezone"` — fixed UTC offset (e.g. `"UTC-8"`), applied to every expanded entry. No DST math.
- `"named_timezone"` — DST-observing zone (e.g. `"PT"`, `"ET"`, `"CT"`, `"MT"`, or full IANA like `"America/Los_Angeles"`). Each field's UTC offset is resolved at its own date, so paper / abstract / notification on different sides of a DST boundary all produce correct UTC instants. Output is normalized to `timezone: "UTC+0"`.

For VLDB specifically, use the [`/vldb`](.claude/skills/vldb/SKILL.md) skill — it knows the Vol-N cycle and the Vol 20+ abstract rule.
```json
{
  "title": "VLDB",
  "year": 2027,
  "venue": "Athens, Greece",
  "start": "2027-08-23",
  "end": "2027-08-27",
  "areas": ["DB"],
  "cfp_link": "https://vldb.org/2027/call-for-research-track.html",
  "frequency": "monthly",
  "first_deadline": {
    "season": "April",
    "paper_deadline": "2026-04-01 17:00:00",
    "abstract_deadline": "2026-03-25 17:00:00",
    "author_notification": "2026-05-15 00:00:00",
    "named_timezone": "PT"
  }
}
```

## Local Development
1. Run `python3 build.py` to generate `public/db.json`
2. Run `python3 -m http.server -d public` to start the HTTP server.

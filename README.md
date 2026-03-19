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

## Local Development
1. Run `python3 build.py` to generate `public/db.json`
2. Run `python3 -m http.server -d public` to start the HTTP server.

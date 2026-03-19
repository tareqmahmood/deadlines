---
name: cfp
description: Search the web for a conference Call for Papers (CFP) and extract structured deadline information into the project's JSON format. Use when the user wants to add a new conference.
argument-hint: [Conference Year, e.g. "Eurosys 2027"]
allowed-tools: WebSearch, WebFetch, Read, Glob, Write, Edit
---

# CFP Search & Extract

Search for Call for Papers information for **$ARGUMENTS** and extract it into this project's conference JSON format.

## Steps

1. **Read existing examples** to understand the exact JSON schema:

!`cat conf/2026/eurosys.json`

!`cat conf/2027/sigmod.json`

2. **Search the web** for the CFP page of $ARGUMENTS. Try queries like:
   - "$ARGUMENTS call for papers"
   - "$ARGUMENTS CFP"
   - "$ARGUMENTS submission deadline"

3. **Fetch the official CFP page** once found, and extract:
   - Conference title (well-known acronym like "EuroSys", "OSDI", "NeurIPS")
   - Year (integer)
   - Venue ("City, Country" or "City, State, Country")
   - Conference start/end dates (YYYY-MM-DD)
   - Areas: pick from `["SYS", "ML", "DB"]` — SYS for systems/architecture/networking, ML for machine learning/AI, DB for databases
   - CFP link (URL)
   - Deadlines array — each entry has:
     - `season`: "Spring", "Fall", etc. or `null` if single round
     - `paper_deadline`: "YYYY-MM-DD HH:MM:SS" or `null`
     - `abstract_deadline`: "YYYY-MM-DD HH:MM:SS" or `null`
     - `author_notification`: "YYYY-MM-DD HH:MM:SS" or `null`
     - `timezone`: e.g. "UTC-12", "UTC-7", "UTC+0"

4. **Show the extracted JSON** to the user and ask for confirmation before saving.

5. **Save** to `conf/{year}/{title_lowercase}.json` (e.g. `conf/2027/eurosys.json`). Create the year directory if needed.

## Important

- Match the exact JSON schema of existing files — no extra fields, no missing fields.
- Use `null` (not empty string) for unknown dates.
- If the CFP page is not yet available, tell the user rather than guessing.
- Warn if the target file already exists.

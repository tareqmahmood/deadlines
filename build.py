import json
import glob
import os
import calendar
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Shorthand → IANA name. Anything not in this map is treated as already-IANA.
NAMED_TIMEZONES = {
    'PT': 'America/Los_Angeles',
    'ET': 'America/New_York',
    'CT': 'America/Chicago',
    'MT': 'America/Denver',
}


def shift_months(dt, n):
    """Return dt advanced by n calendar months, clamping the day to the target
    month's length (e.g. Jan 31 + 1 month → Feb 28/29)."""
    total = dt.year * 12 + (dt.month - 1) + n
    new_year, new_month = total // 12, total % 12 + 1
    day = min(dt.day, calendar.monthrange(new_year, new_month)[1])
    return dt.replace(year=new_year, month=new_month, day=day)


def expand_monthly(conf):
    """For frequency:monthly conferences, expand `first_deadline` into 12
    consecutive monthly entries in `deadlines`. Each field shifts by i months
    from its own template value, so cross-month offsets (e.g. abstract on the
    25th of the previous month) are preserved.

    Timezone handling — exactly one of these is required on the template:
      - `timezone` (e.g. "UTC-8"): fixed offset, applied to all fields and
        copied through to each expanded entry.
      - `named_timezone` (e.g. "PT" or "America/Los_Angeles"): each field is
        resolved at its own local datetime, so paper / abstract / notification
        on different sides of a DST boundary still produce the correct UTC
        instant. Output is normalized to `timezone: "UTC+0"` for the parser;
        `named_timezone` is dropped."""
    if conf.get('frequency') != 'monthly':
        return
    template = conf.pop('first_deadline', None)
    if not template:
        return

    named_tz = template.get('named_timezone')
    fixed_tz = template.get('timezone')
    if named_tz and fixed_tz:
        raise ValueError(
            f"{conf.get('title')} {conf.get('year')}: first_deadline cannot set "
            f"both 'timezone' and 'named_timezone' — pick one."
        )
    if not named_tz and not fixed_tz:
        raise ValueError(
            f"{conf.get('title')} {conf.get('year')}: first_deadline needs "
            f"either 'timezone' or 'named_timezone'."
        )
    zone = ZoneInfo(NAMED_TIMEZONES.get(named_tz, named_tz)) if named_tz else None

    deadlines = []
    for i in range(12):
        entry = dict(template)
        entry.pop('named_timezone', None)
        local_paper = None
        for date_field in ['paper_deadline', 'abstract_deadline', 'author_notification']:
            val = template.get(date_field)
            if not val:
                continue
            shifted = shift_months(datetime.strptime(val, '%Y-%m-%d %H:%M:%S'), i)
            if date_field == 'paper_deadline':
                local_paper = shifted
            if zone is not None:
                utc_dt = shifted.replace(tzinfo=zone).astimezone(timezone.utc).replace(tzinfo=None)
                entry[date_field] = utc_dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                entry[date_field] = shifted.strftime('%Y-%m-%d %H:%M:%S')

        entry['season'] = local_paper.strftime('%B')
        if zone is not None:
            entry['timezone'] = 'UTC+0'
        deadlines.append(entry)

    conf['deadlines'] = deadlines

# Data structures
conferences = []
areas = set()

# Find current year
current_year = datetime.now().year
print(f"Current year detected as: {current_year}")

# Find all years from conf directories
all_years = os.listdir('conf')

# Filter years to only include current year and future years
selected_year = [year for year in all_years if year.isdigit() and int(year) >= current_year]
max_year = max([int(year) for year in selected_year]) if selected_year else current_year

# load conference data from selected years
for year in selected_year:
    conf_files = glob.glob(os.path.join('conf', year, '*.json'))
    for conf_file in conf_files:
        try:
            with open(conf_file, 'r') as conf_fid:
                conf_data = json.load(conf_fid)
                
                # Add derived fields
                conf_data['id'] = f"{conf_data['title'].lower()}-{conf_data['year']}"
                file_id = os.path.splitext(os.path.basename(conf_file))[0]
                conf_data['fileId'] = file_id

                expand_monthly(conf_data)

                conferences.append(conf_data)
                
                if 'areas' in conf_data:
                    for area in conf_data['areas']:
                        areas.add(area)
                        
        except Exception as e:
            print(f"Error reading {conf_file}: {e}")


# Estimate missing conferences from previous year
prev_year = max_year - 1
if str(prev_year) in all_years:
    prev_conf_files = glob.glob(os.path.join('conf', str(prev_year), '*.json'))
    existing_ids = {conf['fileId'] for conf in conferences if conf['year'] == max_year}
    
    for conf_file in prev_conf_files:
        file_id = os.path.splitext(os.path.basename(conf_file))[0]
        if file_id not in existing_ids:
            try:
                with open(conf_file, 'r') as conf_fid:
                    estm_data = json.load(conf_fid)

                    # Skip estimation for monthly/rolling venues — those CFPs are
                    # typically published well in advance, so a synthetic
                    # +1-year placeholder would be misleading.
                    if estm_data.get('frequency') == 'monthly':
                        continue

                    # Create estimated entry for max_year
                    estm_data['year'] = max_year
                    estm_data['id'] = f"{estm_data['title'].lower()}-{max_year}"
                    estm_data['fileId'] = file_id
                    estm_data["is_estimated"] = True
                    estm_data['venue'] = "TBD"
                    estm_data['cfp_link'] = ""

                    # add one year to dates if they exist
                    def add_one_year(date_str):
                        # format '2026-04-01 23:59:59' or '2026-04-01'
                        # detect format
                        if ' ' in date_str:
                            date_format = '%Y-%m-%d %H:%M:%S'
                        else:
                            date_format = '%Y-%m-%d'
                        d_obj = datetime.strptime(date_str, date_format)
                        # add one year
                        try:
                            new_date = d_obj.replace(year=d_obj.year + 1)
                        except ValueError:
                            # handle February 29th for leap years
                            new_date = d_obj.replace(year=d_obj.year + 1, day=28)
                        return new_date.strftime(date_format)
                        
                    # Shift start and end dates
                    for date_field in ['start', 'end']:
                        if date_field in estm_data:
                            estm_data[date_field] = add_one_year(estm_data[date_field])

                    # Shift deadlines if it exists
                    season_deadlines = estm_data.get('deadlines', [])
                    estm_data['deadlines'] = []
                    for season_deadline in season_deadlines:
                        for date_field in ['paper_deadline', 'abstract_deadline', 'author_notification']:
                            if date_field in season_deadline and season_deadline[date_field]:
                                season_deadline[date_field] = add_one_year(season_deadline[date_field])
                        estm_data['deadlines'].append(season_deadline)

                    conferences.append(estm_data)

                    if 'areas' in estm_data:
                        for area in estm_data['areas']:
                            areas.add(area)
                            
            except Exception as e:
                print(f"Error reading {conf_file} for estimation: {e}")


# Sort conferences by year (desc) then title (asc)
conferences.sort(key=lambda x: (-int(x['year']), x['title']))

db = {
    "conferences": conferences,
    "areas": sorted(list(areas)),
    "last_updated": datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
}

# Write to public/db.json
os.makedirs('public', exist_ok=True)
with open('public/db.json', 'w') as db_file:
    json.dump(db, db_file, separators=(',', ':'))

print(f"Generated public/db.json with {len(conferences)} conferences and {len(areas)} areas.")

# Build HTML pages from templates
import re

with open('templates/base.html', 'r') as f:
    base_template = f.read()

active_pages = ['index', 'calendar', 'about']

for template_file in glob.glob('templates/*.html'):
    name = os.path.basename(template_file)
    if name == 'base.html':
        continue

    with open(template_file, 'r') as f:
        page_source = f.read()

    # Parse frontmatter comments
    title = re.search(r'<!-- title: (.+?) -->', page_source).group(1)
    active = re.search(r'<!-- active: (.*?) ?-->', page_source).group(1)
    content = re.sub(r'<!-- (?:title|active): .*?-->\n?', '', page_source).strip()

    # Build page from base
    html = base_template.replace('{{TITLE}}', title)
    html = html.replace('{{CONTENT}}', content)
    for page_name in active_pages:
        placeholder = '{{ACTIVE_' + page_name + '}}'
        html = html.replace(placeholder, 'class="active"' if active == page_name else '')

    output_path = os.path.join('public', name)
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Built {output_path}")

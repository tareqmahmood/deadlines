import json
import glob
import os
from datetime import datetime

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
    "areas": sorted(list(areas))
}

# Write to public/db.json
os.makedirs('public', exist_ok=True)
with open('public/db.json', 'w') as db_file:
    json.dump(db, db_file, separators=(',', ':'))

print(f"Generated public/db.json with {len(conferences)} conferences and {len(areas)} areas.")

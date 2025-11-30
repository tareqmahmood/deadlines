import json
import glob
import os
from datetime import datetime

conferences = []
areas = set()
loaded_data = {} # year (int) -> { fileId -> data }

# 1. Read all existing data
for year_dir in glob.glob('conf/*/'):
    year_str = os.path.basename(os.path.normpath(year_dir))
    try:
        year = int(year_str)
    except ValueError:
        continue
        
    if year not in loaded_data:
        loaded_data[year] = {}

    for f in glob.glob(os.path.join(year_dir, '*.json')):
        try:
            with open(f, 'r') as read_file:
                data = json.load(read_file)
                
                # Add derived fields
                data['id'] = f"{data['title'].lower()}-{data['year']}"
                file_id = os.path.splitext(os.path.basename(f))[0]
                data['fileId'] = file_id
                
                conferences.append(data)
                
                if 'areas' in data:
                    for area in data['areas']:
                        areas.add(area)
                
                loaded_data[year][file_id] = data
                
        except Exception as e:
            print(f"Error reading {f}: {e}")

# 2. Estimate logic
# Find max year from directories
all_years = []
for year_dir in glob.glob('conf/*/'):
    try:
        y = int(os.path.basename(os.path.normpath(year_dir)))
        all_years.append(y)
    except:
        pass

if all_years:
    max_year = max(all_years)
    prev_year = max_year - 1
    
    print(f"Max year: {max_year}, Checking against: {prev_year}")
    
    if prev_year in loaded_data:
        for file_id, prev_data in loaded_data[prev_year].items():
            # Check if this conference exists in max_year
            exists_in_max = False
            if max_year in loaded_data and file_id in loaded_data[max_year]:
                exists_in_max = True
            
            if not exists_in_max:
                print(f"Estimating {prev_data['title']} for {max_year} (based on {prev_year})")
                
                est_conf = prev_data.copy()
                est_conf['year'] = max_year
                est_conf['id'] = f"{est_conf['title'].lower()}-{max_year}"
                est_conf['is_estimated'] = True
                est_conf['venue'] = "TBD"
                est_conf['cfp_link'] = ""
                
                # Shift start/end dates
                for date_field in ['start', 'end']:
                    if date_field in est_conf:
                        try:
                            d_obj = datetime.strptime(est_conf[date_field], "%Y-%m-%d")
                            try:
                                new_d_obj = d_obj.replace(year=d_obj.year + 1)
                            except ValueError:
                                new_d_obj = d_obj + (datetime(d_obj.year + 1, 3, 1) - datetime(d_obj.year, 3, 1))
                            est_conf[date_field] = new_d_obj.strftime("%Y-%m-%d")
                        except Exception as e:
                            print(f"Failed to shift {date_field} date for {est_conf['title']}: {e}")

                # Shift dates +1 year
                new_deadlines = []
                for d in prev_data.get('deadlines', []):
                    new_d = d.copy()
                    try:
                        p_date = datetime.strptime(d['paper_deadline'], "%Y-%m-%d %H:%M:%S")
                        # Add 1 year safely
                        try:
                            new_p_date = p_date.replace(year=p_date.year + 1)
                        except ValueError: # Leap year case
                            new_p_date = p_date + (datetime(p_date.year + 1, 3, 1) - datetime(p_date.year, 3, 1))

                        new_d['paper_deadline'] = new_p_date.strftime("%Y-%m-%d %H:%M:%S")
                        
                        if d.get('abstract_deadline'):
                            a_date = datetime.strptime(d['abstract_deadline'], "%Y-%m-%d %H:%M:%S")
                            try:
                                new_a_date = a_date.replace(year=a_date.year + 1)
                            except ValueError:
                                new_a_date = a_date + (datetime(a_date.year + 1, 3, 1) - datetime(a_date.year, 3, 1))
                            new_d['abstract_deadline'] = new_a_date.strftime("%Y-%m-%d %H:%M:%S")
                        
                        new_d['author_notification'] = "TBD"
                        new_deadlines.append(new_d)
                    except Exception as e:
                        print(f"Failed to shift dates for {est_conf['title']}: {e}")
                
                est_conf['deadlines'] = new_deadlines
                conferences.append(est_conf)

# Sort conferences by year (desc) then title (asc)
conferences.sort(key=lambda x: (-int(x['year']), x['title']))

output = {
    "conferences": conferences,
    "areas": sorted(list(areas))
}

# Write to public/db.json
os.makedirs('public', exist_ok=True)
with open('public/db.json', 'w') as outfile:
    json.dump(output, outfile, separators=(',', ':'))

print(f"Generated public/db.json with {len(conferences)} conferences and {len(areas)} areas.")

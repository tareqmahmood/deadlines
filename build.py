import json
import glob
import os

conferences = []
areas = set()

# Walk through conf directory
# Structure: conf/YEAR/filename.json
for year_dir in glob.glob('conf/*/'):
    year = os.path.basename(os.path.normpath(year_dir))
    for f in glob.glob(os.path.join(year_dir, '*.json')):
        try:
            with open(f, 'r') as read_file:
                data = json.load(read_file)
                
                # Add derived fields that were previously calculated in JS
                data['id'] = f"{data['title'].lower()}-{data['year']}"
                data['fileId'] = os.path.splitext(os.path.basename(f))[0]
                
                conferences.append(data)
                
                if 'areas' in data:
                    for area in data['areas']:
                        areas.add(area)
        except Exception as e:
            print(f"Error reading {f}: {e}")

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

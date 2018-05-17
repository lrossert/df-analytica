import sys
import match_goals
import json

for f in open("filepaths.json", 'r'):
    file_paths = json.loads(f)

for file_path in file_paths:
    match = match_goals.Match(file_path)
    if match.start_data:
        print("SUCCESS *********")
        print(match.match_start_odds)
        if not match.match_odds_data:
            print("error")
            print(match.odds_file)
            sys.exit()

print("Number of available matches: {0}".format(len(file_paths)))

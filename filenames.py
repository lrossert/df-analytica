import os
import sys
import json
import match_goals

data_dir = 'data/xds/historic/BASIC'

def read_odds_file(odds_file):
    """Read the Betfair Odds Data files, returns a list of dicts.

    Note that the files come in a list of dictionaries in 
    json format so we need to unwrap these.
    """
    data = []
    for line in open(odds_file, 'r'):
        data.append(json.loads(line))
    return data

match_odds_filenames = []
for folder, subfolders, files in os.walk(data_dir, 'w'):
    for file_ in files:
        if not file_.endswith('.bz2') and not file_.startswith('.'):
            file_path = os.sep.join([folder] + subfolders + [file_])
            data_info = read_odds_file(file_path)[0]
            # Get file corresponding to the match odds
            if "marketType" in data_info["mc"][0]["marketDefinition"]\
            and data_info["mc"][0]["marketDefinition"]["status"]=="OPEN"\
            and data_info["mc"][0]["marketDefinition"]["marketType"]=="MATCH_ODDS":
                try:
                    match = match_goals.Match(file_path)
                    if match.start_data\
                    and match.start_data["mc"][0]["marketDefinition"]["marketType"]=="MATCH_ODDS":
                        print("{0} added to cache".format(file_path))
                        match_odds_filenames.append(file_path)
                except UnboundLocalError as e:
                    print(e)
                    print("UnboundLocalError for: {0}. Odds for the wrong events appear in this file".format(file_path))
                except IndexError as e:
                    print(e)
                    print("IndexError for: {0}".format(file_path))
                    sys.exit()
                except TypeError as e:
                    print("No odds data for: {0}".format(file_path))
                    
print("Writing caching file")
# cache list of filepaths
with open('filepaths.json', 'w') as f:
    json.dump(match_odds_filenames, f)

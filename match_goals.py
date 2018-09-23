import json
import sys
import copy
import pandas as pd
import numpy as np

#odds_file = "data/xds/historic/BASIC/28522440/1.138129751" 
#odds_file = "data/xds/historic/BASIC/28553681/1.139123056" 
odds_file = "data/xds/historic/BASIC/28521533/1.138102654"
odds_file = "data/xds/historic/BASIC/28525933/1.138270650"

class Match():

    def __init__(self, odds_file):
        self.odds_file = odds_file
        self.data = self.read_odds_file(self.odds_file)
        self.events = self.get_events(self.data)
        self.start_data = self.match_start_data(self.events)
        if self.start_data:
            self.start_idx = self.get_start_idx()
            self.draw_id, self.home_id, self.away_id = self.get_ids()
            self.outcomes = list(self.get_ids())
            self.match_start_odds = self.get_draw_odds_1_min_before_start()
            self.end_idx = self.get_end_idx()
            self.match_odds_data = self.get_match_odds_data()


    def read_odds_file(self, odds_file):
        """Read the Betfair Odds Data files, returns a list of dicts.
    
        Note that the files come in a list of dictionaries in 
        json format so we need to unwrap these.
        """
        data = []
        for line in open(odds_file, 'r'):
            data.append(json.loads(line))
        return data
    
    def get_events(self, data):
        """Returns a list of the major events in the data.
        
        These include match start, end and goals."""
        events = []
        for entry in data:
            if "marketDefinition" in entry["mc"][0]:
                events.append(entry)
        return events
    
    def match_start_data(self, events):
        """Returns the match start dict from the events."""
        for event in events:
            if event["mc"][0]["marketDefinition"]["inPlay"]:
                return event
    
    def get_ids(self):
        """Returns the unique ids for draw, home and away teams."""
        event_ids = self.start_data["mc"][0]["marketDefinition"]["runners"]
        for event_id in event_ids:
            if event_id["name"]=="The Draw":
                draw = event_id["id"]
            elif event_id["sortPriority"]==1:
                home = event_id["id"]
            elif event_id["sortPriority"]==2:
                away = event_id["id"]
            else:
                print("Can't retrieve odds IDs")
        return draw, home, away

    def get_start_idx(self):
        start_idx = 0
        for entry in self.data:
            if entry==self.start_data:
                break
            start_idx = start_idx + 1
        return start_idx
                    
    def get_draw_odds_1_min_before_start(self):
        """Returns the dict of odds  of draw before the start of the game."""
        # get the line where the match starts and iterate backwards
        # findind where draw odds are present
        for odds_idx in range(self.start_idx-1, -1, -1):
            try:
                for odds in self.data[odds_idx]["mc"][0]["rc"]:
                    if odds["id"]==self.draw_id:
                        return odds["ltp"]
            except KeyError as e:
                print("No odds data in entry no: {0}. So take odds from the entry before that".format(odds_idx))
        print("No odds corresponding to the draw. So cannot execute strategy.")
    
    def get_end_idx(self):
        start_idx = 0
        for entry in self.data:
            if entry==self.events[-1]:
                break
            start_idx = start_idx + 1
        return start_idx
    
    def _get_outcome_odds(self, outcome_id, goal_idx):
        """Returns dict of odds by outcome_id.
    
        Used in the fucntion _get_odds_before_goal."""
                # get last odd of each id
        for odds_idx in range(goal_idx-2, -1, -1):
            try:
                for odds in self.data[odds_idx]["mc"][0]["rc"]:
                    if odds["id"]==outcome_id:
                        return odds
            except KeyError:
                print("Match coming to an ended.")
    
    def _get_odds_before_goal(self, goal):
        """Returns a list of odds for all outcomes \
        before the goal happened."""
        goal_idx = 0
        for entry in self.data:
            if entry==goal:
                break
            goal_idx = goal_idx + 1
        pre_goal_odds = list()
        for outcome_id in self.outcomes:
            odds = self._get_outcome_odds(outcome_id, goal_idx) 
            pre_goal_odds.append(odds)
        return pre_goal_odds
    
    def _prettify_odds(self, odds_list_of_dicts):
        """Returns odds dict with associated key of outcome_id"""
        odds_dict = dict()
        for odds_idx in range(len(odds_list_of_dicts)):
            odds = odds_list_of_dicts[odds_idx]
            odds_dict_entry = {odds["id"]: odds["ltp"]}
            odds_dict.update(odds_dict_entry)
        return odds_dict       

    def get_match_odds_data(self):
        """Returns a list of dicts of times and odds at those times.
        Where odds are not available take the previous odds as a proxy."""
        match_data = []
        prev_formatted_odds = None
        for odds_idx in range(self.start_idx+1, self.end_idx+1):
            odds = self.data[odds_idx]
            clk = odds["clk"]
            try:
                formatted_odds  = self._prettify_odds(odds["mc"][0]["rc"])
                if self.draw_id in formatted_odds.keys():
                    formatted_odds["draw_odds"] = formatted_odds.pop(self.draw_id)
                if self.home_id in formatted_odds.keys():
                    formatted_odds["home_odds"] = formatted_odds.pop(self.home_id)
                if self.away_id in formatted_odds.keys():
                    formatted_odds["away_odds"] = formatted_odds.pop(self.away_id)
                formatted_odds.update({"clk": clk})
                # Make the assmption that if the odds are not given they havent
                # changed from the previous odds.
                if prev_formatted_odds \
                and "away_odds" not in formatted_odds.keys() \
                and "away_odds" in prev_formatted_odds.keys():
                    formatted_odds["away_odds"] = prev_formatted_odds["away_odds"] 
                if prev_formatted_odds \
                and "home_odds" not in formatted_odds.keys() \
                and "home_odds" in prev_formatted_odds.keys():
                    formatted_odds["home_odds"] = prev_formatted_odds["home_odds"] 
                if prev_formatted_odds \
                and "draw_odds" not in formatted_odds.keys() \
                and "draw_odds" in prev_formatted_odds.keys():
                    formatted_odds["draw_odds"] = prev_formatted_odds["draw_odds"] 
                prev_formatted_odds = formatted_odds
                match_data.append(formatted_odds)
            except KeyError as e:
                print("No odds available. Match coming towards an end at time {0}"\
                .format(clk))
        return pd.DataFrame(match_data)

if __name__ == "__main__":
    match = Match(odds_file)
    print(match.match_odds_data)


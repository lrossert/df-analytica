import json
import sys
import copy

odds_file = "data/xds/historic/BASIC/28522440/1.138129751" 
#odds_file = "data/xds/historic/BASIC/28553681/1.139123056" 

class Match():

    def __init__(self, odds_file):
        self.odds_file = odds_file
        self.data = self.read_odds_file(self.odds_file)
        self.events = self.get_events(self.data)
        self.start_data = self.match_start_data(self.events)
        self.start_idx = self.get_start_idx()
        self.draw_id, self.home_id, self.away_id = self.get_ids()
        self.outcomes = list(self.get_ids())
        self.match_start_odds = self.get_draw_odds_1_min_before_start()
        self.goal_data = self.match_goal_data()
        print(self.goal_data)
        self.end_idx = self.get_end_idx()
        self.goals = self.get_goals()
        self.match_data = self.get_match_data()

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
            for odds in self.data[odds_idx]["mc"][0]["rc"]:
                if odds["id"]==self.draw_id:
                    return odds["ltp"]
        print("No odds corresponding to the draw")
    
    def match_goal_data(self):
        """Returns list of dicts of events when goals occur."""
        start_idx = 0
        for event in self.events:
            if event==self.start_data:
                break
            start_idx = start_idx + 1
        goal_data = self.events[start_idx+1:]
        # remove closing odds
        goal_data = goal_data[:-2]
        # there are 2 entries for every goal so we take the second ones
        goal_data = [goal_data[goal_idx] for goal_idx in range(len(goal_data))\
                        if goal_idx%2==1]
        return goal_data

    def get_end_idx(self):
        start_idx = 0
        for entry in self.data:
            if entry==self.goal_data[-1]:
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
        for odds in odds_list_of_dicts:
            odds_dict_entry = {odds["id"]: odds["ltp"]}
            odds_dict.update(odds_dict_entry)
        return odds_dict       

    def check_goal_scored(self, goal_dict, goal_list, goal, clk):
        odds_after_goal = self._prettify_odds(goal["mc"][0]["rc"])
        if not goal_dict:
            print("Making goal_dict")
            goal_dict = {"clk": clk, self.home_id: 0, self.away_id: 0}
        else:
            goal_dict = copy.deepcopy(goal_dict)
            goal_dict["clk"] = clk
        odds_before_goal = self._get_odds_before_goal(goal)
        odds_before_goal = self._prettify_odds(odds_before_goal)
        if odds_before_goal[self.home_id] < odds_after_goal[self.home_id]\
        and odds_before_goal[self.away_id] > odds_after_goal[self.away_id]:
            goal_dict[self.away_id] = goal_dict[self.away_id] + 1
        elif odds_before_goal[self.home_id] > odds_after_goal[self.home_id]\
        and odds_before_goal[self.away_id] < odds_after_goal[self.away_id]:
            goal_dict[self.home_id] = goal_dict[self.home_id] + 1
        else:
            print("Can't conclude there was a goal")
        goal_list.append(goal_dict)
        return goal_list


    
    def get_goals(self):
        """Returns a list of scores at clk times when the goals happen.
    
        Compares the odds just before the goal event to the odds after
        to estimate which team scored."""
        goal_list = []
        goal_dict = {}
        for goal in self.goal_data:
            clk = goal["clk"]
            try:
                goal_list = self.check_goal_scored(goal_dict, goal_list, goal, clk)
            except KeyError:
                print("No odds available. Match coming towards an end at time {0}"\
                .format(goal["clk"]))
        return goal_list
    
    def get_match_data(self):
        # the followinf should not be hard coded but attributes of the class
        match_data = []
        for odds_idx in range(self.start_idx+1, self.end_idx+1):
            score_dict = {self.home_id: 0, self.away_id: 0}
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
                for goal in self.goals:
                    goal_clk = goal["clk"]
                    if int(clk) >= int(goal_clk):
                        score_dict = copy.deepcopy(goal)
                    score_dict["clk"] = clk
                # Note this overides the team odds but we are
                # only concerned with draw odds in our strategy
                formatted_odds.update(score_dict)
                match_data.append(formatted_odds)
            except KeyError:
                print("No odds available. Match coming towards an end at time {0}"\
                .format(goal["clk"]))
        return match_data
    

if __name__ == "__main__":
    match = Match(odds_file)

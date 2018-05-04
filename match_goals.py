import json
import sys
import copy

odds_file = "data/xds/historic/BASIC/28522440/1.138129751" 

def read_odds_file(odds_file):
    """Read the Betfair Odds Data files, returns a list of dicts.

    Note that the files come in a list of dictionaries in 
    json format so we need to unwrap these.
    """
    data = []
    for line in open(odds_file, 'r'):
        data.append(json.loads(line))
    return data

def get_events(data):
    """Returns a list of the major events in the data.
    
    These include match start, end and goals."""
    events = []
    for entry in data:
        if "marketDefinition" in entry["mc"][0]:
            events.append(entry)
    return events

def match_start_data(events):
    """Returns the match start dict from the events."""
    for event in events:
        if event["mc"][0]["marketDefinition"]["inPlay"]:
            return event

def get_ids(start_data):
    """Returns the unique ids for draw, home and away teams."""
    event_ids = start_data["mc"][0]["marketDefinition"]["runners"]
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
                
def get_draw_odds_1_min_before_start(data):
    """Returns the dict of odds  of draw before the start of the game."""
    # get the line where the match starts and iterate backwards
    # findind where draw odds are present
    events = get_events(data)
    start_data = match_start_data(events)
    start_idx = 0
    for entry in data:
        if entry==start_data:
            break
        start_idx = start_idx + 1
    draw_id = get_ids(start_data)[0]
    for odds_idx in range(start_idx-1, -1, -1):
        for odds in data[odds_idx]["mc"][0]["rc"]:
            if odds["id"]==draw_id:
                return odds["ltp"]
    print("No odds corresponding to the draw")

def match_goal_data(events):
    """Returns list of dicts of events when goals occur."""
    start_data = match_start_data(events)
    start_idx = 0
    for event in events:
        if event==start_data:
            break
        start_idx = start_idx + 1
    goal_data = events[start_idx+1:]
    # remove closing odds
    goal_data = goal_data[:-2]
    # there are 2 entries for every goal so we take the second ones
    goal_data = [goal_data[goal_idx] for goal_idx in range(len(goal_data))\
                    if goal_idx%2==1]
    return goal_data

def _get_outcome_odds(outcome_id, data, goal_idx):
    """Returns dict of odds by outcome_id.

    Used in the fucntion _get_odds_before_goal."""
            # get last odd of each id
    for odds_idx in range(goal_idx-2, -1, -1):
        try:
            for odds in data[odds_idx]["mc"][0]["rc"]:
                if odds["id"]==outcome_id:
                    return odds
        except KeyError:
            print("Match coming to an ended.")

def _get_odds_before_goal(goal, data):
    """Returns a list of odds for all outcomes \
    before the goal happened."""

    events = get_events(data)
    start_data = match_start_data(events)
    outcomes = list(get_ids(start_data))
    goal_idx = 0
    for entry in data:
        if entry==goal:
            break
        goal_idx = goal_idx + 1
    pre_goal_odds = list()
    for outcome_id in outcomes:
        odds =_get_outcome_odds(outcome_id, data, goal_idx) 
        pre_goal_odds.append(odds)
    return pre_goal_odds

def _prettify_odds(odds_list_of_dicts):
    """Returns odds dict with associated key of outcome_id"""
    odds_dict = dict()
    for odds in odds_list_of_dicts:
        odds_dict_entry = {odds["id"]: odds["ltp"]}
        odds_dict.update(odds_dict_entry)
    return odds_dict       

def get_goals(goal_data, data):
    """Returns a list of scores at clk times when the goals happen.

    Compares the odds just before the goal event to the odds after
    to estimate which team scored."""
    events = get_events(data)
    start_data = match_start_data(events)
    draw_id, home_id, away_id = get_ids(start_data)
    goals_list = []
    goal_dict = {}
    for goal in goal_data:
        clk = goal["clk"]
        try:
            odds_after_goal = _prettify_odds(goal["mc"][0]["rc"])
            if not goal_dict:
                print("Making goal_dict")
                goal_dict = {"clk": clk, home_id: 0, away_id: 0}
            else:
                goal_dict = copy.deepcopy(goal_dict)
                goal_dict["clk"] = clk
            odds_before_goal = _get_odds_before_goal(goal, data)
            odds_before_goal = _prettify_odds(odds_before_goal)
            # need to compare these odds to the previous ones to see if there was a goal or not
            if odds_before_goal[home_id] < odds_after_goal[home_id]\
            and odds_before_goal[away_id] > odds_after_goal[away_id]:
                goal_dict[away_id] = goal_dict[away_id] + 1
            elif odds_before_goal[home_id] > odds_after_goal[home_id]\
            and odds_before_goal[away_id] < odds_after_goal[away_id]:
                goal_dict[home_id] = goal_dict[home_id] + 1
            else:
                print("Can't conclude there was a goal")
            goals_list.append(goal_dict)
        except KeyError:
            print("No odds available. Match coming towards an end at time {0}"\
            .format(goal["clk"]))
    print(goals_list)
    return goals_list
    

if __name__ == "__main__":
    data = read_odds_file(odds_file)
    events = get_events(data)
    start_data = match_start_data(events)
    draw_id = get_ids(start_data)
    draw_odds = get_draw_odds_1_min_before_start(data)

    goal_data = match_goal_data(events)
    _prettify_odds([{u'ltp': 1.89, u'id': 6480414}, {u'ltp': 4.8, u'id': 3862627}])
    goals = get_goals(goal_data, data)
